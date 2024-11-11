import mysql.connector
import pandas as pd
from flask import Flask, request, jsonify
import base64
import cv2
import numpy as np
import face_recognition
app = Flask(__name__)



@app.route('/validar_rosto', methods=['POST'])
def reconhecer():
    # Pega os dados JSON da requisição
    data = request.get_json()

    # Pega a imagem Base64
    imagem_base64 = data['imagem']

    # Converte a imagem de Base64 para binário
    img_data = base64.b64decode(imagem_base64)
    np_arr = np.frombuffer(img_data, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # Detecção de rosto usando a biblioteca face_recognition
    face_locations = face_recognition.face_locations(image)

    if not face_locations:
        return jsonify({"mensagem": "Nenhum rosto detectado."})

    # Retorna a quantidade de rostos detectados
    return jsonify({"mensagem": f"{len(face_locations)} rosto(s) detectado(s)."})





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
