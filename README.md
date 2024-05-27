# Projeto de Análise Meteorológica para Cidades do Rio Grande do Sul

Este é um projeto que visa fornecer análises meteorológicas para várias cidades localizadas no estado do Rio Grande do Sul, Brasil. Ele utiliza dados meteorológicos em tempo real de uma API pública para calcular estatísticas como temperatura, precipitação, velocidade do vento, pressão atmosférica e radiação solar. Com essas informações, o projeto determina o nível de risco meteorológico para cada cidade.

## Funcionalidades

- **Obtenção de Dados**: O projeto utiliza a API da Open Meteo para obter dados meteorológicos atualizados para as cidades do Rio Grande do Sul.
  
- **Cálculo de Estatísticas**: Com base nos dados obtidos, o projeto calcula estatísticas como temperatura mínima e máxima, quantidade de precipitação, velocidade máxima do vento, média de probabilidade de precipitação, média de pressão atmosférica e média de radiação solar direta.

- **Avaliação de Risco**: Utilizando as estatísticas calculadas, o projeto determina o nível de risco meteorológico para cada cidade. São considerados fatores como alta precipitação, velocidade do vento, temperaturas extremas, baixa pressão atmosférica e alta radiação solar.

## Pré-requisitos

- Python 3.7 ou superior
- Bibliotecas Python: aiohttp, pandas, dotenv

## Instalação

1. Clone o repositório para o seu ambiente local:

```bash
git clone https://github.com/8b1tz/informa-clima
```

2. Instale as dependências necessárias:

```bash
pip install -r requirements.txt
```

## Uso

Execute o script principal para obter e analisar os dados meteorológicos:

```bash
uvicorn src.main.py:app --reload
```


## Criado por:

- Backend: Yohanna de Oliveira 
- Frontend: Ana Júlia Lins [https://github.com/AnaLinsDev/womankers_rs](repositório)

