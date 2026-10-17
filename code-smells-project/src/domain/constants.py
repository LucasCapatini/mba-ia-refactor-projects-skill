"""Constantes e enumerações do domínio da loja.

Os valores são idênticos aos que estavam espalhados pelos handlers originais;
apenas ganharam nome e um único lugar.
"""

APP_VERSION = "1.0.0"

# Produtos
CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

# Usuários
TIPO_USUARIO_PADRAO = "cliente"

# Pedidos
STATUS_PEDIDO_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]
STATUS_PEDIDO_INICIAL = "pendente"

# Relatório de vendas: (limite inferior exclusivo do faturamento, percentual de desconto)
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))
