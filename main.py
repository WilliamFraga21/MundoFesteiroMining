import mysql.connector
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
from PIL import Image
from io import BytesIO

import face_recognition
import numpy as np
import json
app = Flask(__name__)

# Permitir requisições de qualquer origem
CORS(app, resources={r"/*": {"origins": "*"}})




# Configuração do banco
def conectar_bd():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="admin",
        database="mundofesteirobd2"
    )

@app.route("/salvar_rosto", methods=["POST"])
def salvar_rosto():
    # Recebe os dados do frontend
    dados = request.get_json()
    users_id = dados.get("users_id")  # ID do usuário
    imagem_base64 = dados.get("imagem")  # Imagem em Base64
    if not users_id or not imagem_base64:
        return jsonify({"erro": "ID do usuário ou imagem ausente", "id": imagem_base64}), 400

    # Remover o prefixo data:image/jpeg;base64, (se houver)
    if imagem_base64.startswith("data:image"):
        imagem_base64 = imagem_base64.split(",")[1]

    # Decodificar a imagem Base64
    try:
        img_data = base64.b64decode(imagem_base64)
        image = Image.open(BytesIO(img_data))
        image = np.array(image)
    except Exception as e:
        return jsonify({"erro": "Erro ao processar a imagem", "detalhes": str(e)}), 400

    # Detecção e Extração de Características
    try:
        face_locations = face_recognition.face_locations(image)
        if not face_locations:
            return jsonify({"erro": "Nenhum rosto encontrado"}), 400

        # Extrair as características do primeiro rosto detectado
        face_encodings = face_recognition.face_encodings(image, face_locations)
        if not face_encodings:
            return jsonify({"erro": "Não foi possível extrair características faciais"}), 400

        encoding = face_encodings[0]  # Pegando o primeiro rosto detectado
    except Exception as e:
        return jsonify({"erro": "Erro no reconhecimento facial", "detalhes": str(e)}), 500

    # Salvar no banco de dados
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        sql = "INSERT INTO faces (users_id, encoding) VALUES (%s, %s)"
        cursor.execute(sql, (users_id, json.dumps(encoding.tolist())))
        conn.commit()
        conn.close()
        return jsonify({"mensagem": "Rosto salvo com sucesso"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500



@app.route("/reconhecer_rosto", methods=["POST"])
def reconhecer_rosto():
    from flask import request, jsonify
    import face_recognition
    import json
    import numpy as np

    # Receber imagem do frontend (em Base64)
    dados = request.get_json()
    imagem_base64 = dados.get("imagem")

    if not imagem_base64:
        return jsonify({"erro": "Imagem não enviada"}), 400

    # Decodificar a imagem Base64
    import base64
    from io import BytesIO
    from PIL import Image

    img_data = base64.b64decode(imagem_base64)
    image = Image.open(BytesIO(img_data))
    image = np.array(image)

    # Detecção e Extração de Características
    face_locations = face_recognition.face_locations(image)
    if not face_locations:
        return jsonify({"erro": "Nenhum rosto encontrado na imagem"}), 400

    # Extrair as características faciais do rosto
    face_encodings = face_recognition.face_encodings(image, face_locations)
    if not face_encodings:
        return jsonify({"erro": "Não foi possível extrair características faciais"}), 400

    # Carregar os rostos conhecidos do banco de dados
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT users_id, encoding FROM faces")
        result = cursor.fetchall()
        conn.close()

        known_face_encodings = []
        known_face_ids = []

        for users_id, encoding in result:
            known_face_ids.append(users_id)
            known_face_encodings.append(np.array(json.loads(encoding)))

        # Comparar com os rostos conhecidos
        encoding_atual = face_encodings[0]
        face_distances = face_recognition.face_distance(known_face_encodings, encoding_atual)
        best_match_index = np.argmin(face_distances)

        if face_distances[best_match_index] < 0.6:  # Limite de similaridade
            users_id = known_face_ids[best_match_index]
            return jsonify({"mensagem": "Rosto reconhecido", "users_id": users_id}), 200
        else:
            return jsonify({"mensagem": "Rosto não reconhecido"}), 404

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


















@app.route('/comparar_rosto', methods=['POST'])
def comparar_rosto():
    try:
        # Debug: Exibe o corpo da requisição recebida como texto
        data_raw = request.get_data(as_text=True)
        print(f"Corpo da requisição: {data_raw}")


        return jsonify({"erro": "Nenhum rosto correspondente encontrado.","dwadwa":data_raw}), 404

    except Exception as e:
        return jsonify({"erro": str(e)}), 500





























# Conexão com o banco de dados
def conectar_ao_banco():
    conn = mysql.connector.connect(
        host="localhost",  # Substitua com o seu host
        user="root",       # Substitua com o seu usuário
        password="admin",  # Substitua com a sua senha
        database="mundofesteirobd2"
    )
    return conn

# Carregar dados da tabela 'itenspedido' e 'pedido'
def carregar_dados():
    conn = conectar_ao_banco()
    query = """
        SELECT i.Quantidade, i.Valor_Uni, i.produtosvariasoes_id, p.Valor_Total, p.Status, p.created_at
        FROM itenspedido i
        JOIN pedido p ON i.pedido_id = p.id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Endpoint para produtos mais vendidos
@app.route('/api/produtos-mais-vendidos', methods=['GET'])
def produtos_mais_vendidos():
    df = carregar_dados()
    produtos_vendidos = df.groupby('produtosvariasoes_id')['Quantidade'].sum().sort_values(ascending=False)
    return jsonify(produtos_vendidos.head().to_dict())

# Endpoint para receita total por produto
@app.route('/api/receita-produto', methods=['GET'])
def receita_produto():
    df = carregar_dados()
    df['Receita'] = df['Quantidade'] * df['Valor_Uni']
    receita_produtos = df.groupby('produtosvariasoes_id')['Receita'].sum().sort_values(ascending=False)
    return jsonify(receita_produtos.head().to_dict())

# Endpoint para o valor médio dos pedidos finalizados
@app.route('/api/valor-medio-pedido', methods=['GET'])
def valor_medio_pedido():
    df = carregar_dados()
    pedidos_finalizados = df[df['Status'] == 'Finalizado']
    valor_medio = pedidos_finalizados['Valor_Total'].mean()
    return jsonify({"valor_medio_pedido": valor_medio})

# Endpoint para pedidos por mês
@app.route('/api/pedidos-por-mes', methods=['GET'])
def pedidos_por_mes():
    # Supomos que 'pedidos_por_mes' seja um DataFrame com dados mensais
    data = {
        'data': pd.date_range(start='2024-01-01', periods=12, freq='M'),
        'quantidade': range(10, 130, 10)
    }
    df = pd.DataFrame(data)

    # Convertendo o índice para string
    df['data'] = df['data'].dt.strftime('%Y-%m')

    # Transformando em uma lista de dicionários serializável
    pedidos_por_mes = df.to_dict(orient='records')
    return jsonify(pedidos_por_mes)

# Endpoint para taxa de conversão por status do pedido
@app.route('/api/taxa-conversao', methods=['GET'])
def taxa_conversao():
    df = carregar_dados()
    taxa_conversao = df['Status'].value_counts(normalize=True).mul(100).round(2).to_dict()
    return jsonify(taxa_conversao)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
