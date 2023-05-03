import pandas as pd

import matplotlib.pyplot as plt

import streamlit as st
from streamlit_folium import st_folium
import streamlit.components.v1 as components

import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objs import Layout

from numerize.numerize import numerize

import geopandas as gpd
from geopandas import GeoDataFrame

import folium

st.set_page_config(page_title='Análise dos dados do TSE',
                   layout='wide',
                   initial_sidebar_state='collapsed')


@st.cache_data
def get_data(dados):
    if (dados == 'Estadual - 1º turno'):
        df = pd.read_csv('data/df_estados_1turno_2020.csv')
    elif (dados == 'Estadual - 2º turno'):
        df = pd.read_csv('data/df_estados_2turno_2020.csv')
    elif (dados == 'Municipal - 1º turno'):
        df = pd.read_csv('data/df_municipios_1turno_2020.csv')
    else:
        df = pd.read_csv('data/df_municipios_2turno_2020.csv')
    return df


df = get_data('Estadual - 1º turno')

header_left, header_mid, header_right = st.columns([1, 2, 1], gap='large')

with header_mid:
    st.title('Análise dos dados do TSE')

dados = st.selectbox(label='Selecione a eleição',
                     options=['Estadual - 1º turno', 'Estadual - 2º turno',
                              'Municipal - 1º turno', 'Municipal - 2º turno'])

df = get_data(dados)

total_eleitores = float(df['aptos'].sum())
total_eleitores_feminino = float(df['eleitorado_feminino'].sum())
total_eleitores_masculino = float(df['eleitorado_masculino'].sum())
comparecimento_percentual = float(df['comparecimento_percentual(%)'].mean())
abstencao_percentual = float(df['abstencao_percentual(%)'].mean())

total1, total2, total3, total4, total5 = st.columns(5, gap='large')

with total1:
    st.image('images/voters.png', use_column_width='Auto')
    st.metric(label='Eleitores aptos', value=numerize(total_eleitores))

with total2:
    st.image('images/mulher.png', use_column_width='Auto')
    st.metric(label='Eleitorado feminino',
              value=numerize(total_eleitores_feminino))

with total3:
    st.image('images/masculino.png', use_column_width='Auto')
    st.metric(label='Eleitorado masculino',
              value=numerize(total_eleitores_masculino))

with total4:
    st.image('images/voto.png', use_column_width='Auto')
    st.metric(label='Comparecimento percentual', value='{:0,.2f}%'.format(
        comparecimento_percentual).replace('.', ','))

with total5:
    st.image('images/votar-nao.png', use_column_width='Auto')
    st.metric(label='Abstenção percentual', value='{:0,.2f}%'.format(
        abstencao_percentual).replace('.', ','))

if ((dados == 'Estadual - 1º turno')
        or (dados == 'Estadual - 2º turno')):

    ESTADOS = (df['estado'].drop_duplicates())

    def format_func_estado(option):
        return ESTADOS[option]

    estado = st.selectbox(
        "", options=list(ESTADOS.keys()), 
        format_func=format_func_estado,
        key='estados')
    
    Q1, Q2 = st.columns(2)
    with Q1:
        st.write('Comparecimento percentual por estado')
        geo = gpd.read_file('data/geo.gpkg', layer='lim_unidade_federacao_a')
        geo.rename({'sigla': 'estado'}, axis=1, inplace=True)
        geo = geo.sort_values(by='estado', ascending=True)
        geo = geo.reset_index(drop=True)
        geo = geo.drop(columns=['nome', 'nomeabrev', 'geometriaaproximada', 'geocodigo',
                                'id_produtor', 'id_elementoprodutor', 'cd_insumo_orgao',
                                'nr_insumo_mes', 'nr_insumo_ano', 'tx_insumo_documento'], axis=1)

        df = df.merge(geo, on='estado', how='inner')
        geoDF = GeoDataFrame(
            df[['estado', 'comparecimento_percentual(%)', 'geometry']])
        m = geoDF.explore(
            column="estado",
            cmap="summer",
            # name="Estados"
        )
        folium.TileLayer('Stamen Toner', control=True).add_to(m)
        folium.LayerControl().add_to(m)
        st_map = st_folium(m, width=680, height=440)

    with Q2:
        def plot_chart(estadoIndex, df):
            estado = format_func_estado(estadoIndex)

            valor = df.loc[(df['estado'] == estado), 'comparecimento_percentual(%)'].values[0]
            fig = go.Figure(
                go.Indicator(
                    value=valor,
                    title={'text': f"Comparecimento percentual em {estado}"},
                    number={'font_color': '#355070', 'suffix': '%',
                            'font_size': 80, "valueformat": ".2f"},
                    align='center'))

            st.plotly_chart(fig, use_container_width=True)

        plot_chart(estado, df)

    st.write('Divisão por sexo por estado')
    Q3, Q4 = st.columns(2)
    with Q3:
        homens = df['eleitorado_masculino_percentual(%)']
        mulheres = df['eleitorado_feminino_percentual(%)']

        homens = homens.drop_duplicates()
        mulheres = mulheres.drop_duplicates()

        estados = df['estado'].drop_duplicates()

        fig = go.Figure()

        fig.add_trace(go.Bar(y=estados, x=homens,
                             name='Homens',
                             hovertemplate='%{y} %{x:.2f}%',
                             marker_color='#355070',
                             orientation='h'))

        fig.add_trace(go.Bar(y=estados,
                             x=mulheres,
                             hovertemplate='%{y} %{x:.2f}%',
                             marker_color='#FCC202',
                             name='Mulheres',
                             orientation='h'))

        fig.update_layout(title='', plot_bgcolor="rgba(0,0,0,0)",
                          title_font_size=22, barmode='relative',
                          hoverlabel=dict(bgcolor='#FFFFFF'),
                          template='simple_white',
                          bargap=0, bargroupgap=0,
                          margin=dict(l=1, r=1, t=60, b=1),
                          xaxis_range=[0, 100],
                          xaxis=dict(tickvals=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                                     ticktext=['0%', '10%', '20%', '30%', '40%', '50%', '60%', '70%', '80%', '90%', '100%']))

        fig.update_traces(width=0.5)

        st.plotly_chart(fig, use_container_width=True)
    
    with Q4:
        #st.write('Divisão por sexo no estado selecionado')
        def plot_chart(estadoIndex, df):
            estado = format_func_estado(estadoIndex)
            nomeEstado = [df.loc[(df['estado'] == estado, 'estado')].values[0]]
            
            homens = [df.loc[(df['estado'] == estado), 
                'eleitorado_masculino_percentual(%)'].values[0]]
            
            mulheres = [df.loc[(df['estado'] == estado), 
                'eleitorado_feminino_percentual(%)'].values[0]]

            my_layout = Layout(hoverlabel=dict(
                bgcolor='#FFFFFF'), template='simple_white')

            fig_sexoEstado = go.Figure()
            fig_sexoEstado.add_trace(go.Bar(y=nomeEstado, x=homens,
                                               name='',
                                               hovertemplate='Homens: %{x:.2f}%',
                                               marker_color='#355070',
                                               orientation='h'))

            fig_sexoEstado.add_trace(go.Bar(y=nomeEstado, x=mulheres,
                                               hovertemplate='Mulheres: %{x:.2f}%',
                                               marker_color='#FCC202',
                                               name='',
                                               orientation='h'))

            fig_sexoEstado.update_layout(barmode='relative',
                                            hoverlabel=dict(bgcolor='#FFFFFF'),
                                            template='simple_white',
                                            bargap=0, bargroupgap=0,
                                            margin=dict(l=1, r=1, t=60, b=1),
                                            xaxis_range=[0, 100],
                                            xaxis=dict(
                                                tickvals=[0, 10, 20, 30, 40,
                                                          50, 60, 70, 80, 90, 100],
                                                ticktext=['0%', '10%', '20%', '30%', '40%', '50%',
                                                          '60%', '70%', '80%', '90%', '100%']))

            fig_sexoEstado.update_traces(width=0.5)
            fig_sexoEstado.update_xaxes(ticksuffix="")
            fig_sexoEstado.update_yaxes(ticksuffix="")
            st.plotly_chart(fig_sexoEstado, use_container_width=True)

        plot_chart(estado, df)

    st.write('Divisão por escolaridade por estado')
    Q5, Q6 = st.columns(2)

    with Q5:
        escolaridade_percentual = df[['estado', 'analfabeto_percentual(%)', 'le_escreve_percentual(%)',
        'fundamental_incompleto_percentual(%)', 'fundamental_completo_percentual(%)', 'medio_incompleto_percentual(%)',
        'medio_completo_percentual(%)', 
        'superior_incompleto_percentual(%)', 'superior_completo_percentual(%)']].sort_values(by = 'superior_completo_percentual(%)', ascending = False)[:10]
        
        x1 = escolaridade_percentual['estado'] 
        analfabeto = escolaridade_percentual['analfabeto_percentual(%)'] 
        le_escreve = escolaridade_percentual['le_escreve_percentual(%)']
        fundamental_incompleto = escolaridade_percentual['fundamental_incompleto_percentual(%)']
        fundamental_completo = escolaridade_percentual['fundamental_completo_percentual(%)']
        medio_incompleto = escolaridade_percentual['medio_incompleto_percentual(%)']
        medio_completo = escolaridade_percentual['medio_completo_percentual(%)']
        superior_incompleto = escolaridade_percentual['superior_incompleto_percentual(%)']
        superior_completo = escolaridade_percentual['superior_completo_percentual(%)']

        my_layout = Layout(hoverlabel = dict(bgcolor = '#FFFFFF'), template = 'simple_white')

        fig = go.Figure(data=[
            go.Bar(name='',x= x1, y=analfabeto, hovertemplate = 'Analfabeto: %{y:.2f}%', marker_color='#355070', showlegend = False),
            go.Bar(name='', x=x1, y=le_escreve, hovertemplate = 'Lê e escreve: %{y:.2f}%', marker_color= '#597092', showlegend = False),
            go.Bar(name='', x= x1, y=fundamental_incompleto, hovertemplate = 'Fundamental incompleto %{y:.2f}%', marker_color='#7179E6', showlegend = False),
            go.Bar(name='', x=x1, y=fundamental_completo, hovertemplate = 'Fundamental completo %{y:.2f}%', marker_color= '#DEE0FC', showlegend = False),
            go.Bar(name='', x= x1, y=medio_incompleto, hovertemplate = 'Médio incompleto: %{y:.2f}%', marker_color='#E9DEFC', showlegend = False),
            go.Bar(name='', x=x1, y=medio_completo, hovertemplate = 'Médio completo: %{y:.2f}%', marker_color= '#FEE592', showlegend = False),
            go.Bar(name='', x= x1, y=superior_incompleto, hovertemplate = 'Superior incompleto: %{y:.2f}%', marker_color='#E6DD39', showlegend = False),
            go.Bar(name='', x=x1, y=superior_completo, hovertemplate = 'Superior completo: %{y:.2f}%', marker_color= '#FCC202', showlegend = False)
        ], layout = my_layout)

        fig.update_layout(
        xaxis=dict(
            rangeslider=dict(
            visible=True
            ),
        ),
        barmode='stack',
        yaxis_range=[0,100],
        yaxis = dict(
            tickvals = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
            ticktext = ['0%', '10%', '20%', '30%', '40%', '50%', '60%', '70%', '80%', '90%', '100%'])
        )

        fig.update_xaxes(ticksuffix = "")
        fig.update_yaxes(ticksuffix = "")

        st.plotly_chart(fig, use_container_width=True)

        #if (dados == 'Estadual - 1º turno'):
        #    htmlFile = open(
        #        "D:\\UFMS\\TCC\\Dashboard\\data\\charts\\estados_1turno\\estadosEscolaridade_1turno.html", 'r', encoding='utf-8')
        #elif (dados == 'Estadual - 2º turno'):
        #    htmlFile = open(
        #        "D:\\UFMS\\TCC\\Dashboard\\data\\charts\\estados_2turno\\estadosEscolaridade_2turno.html", 'r', encoding='utf-8')
        #elif (dados == 'Municipal - 1º turno'):
        #    htmlFile = open(
        #        "D:\\UFMS\\TCC\\Dashboard\\data\\charts\\municipios_1turno\\municipiosEscolaridade_1turno.html", 'r', encoding='utf-8')
        #else:
        #    htmlFile = open(
        #        "D:\\UFMS\\TCC\\Dashboard\\data\\charts\\municipios_2turno\\municipiosEscolaridade_2turno.html", 'r', encoding='utf-8')
        #source_code = htmlFile.read()
        #components.html(source_code, height=480)

        with Q6:
            #ESCOLARIDADE POR ESTADO
            # st.write('Divisão por escolaridade por estado')

            def plot_chart(estadoIndex, df):

                estado = format_func_estado(estadoIndex)
                nomeEstado = [df.loc[(df['estado'] == estado, 'estado')].values[0]]

                analfabeto = [df.loc[(df['estado'] == estado), 'analfabeto_percentual(%)'].values[0]]
                le_escreve = [df.loc[(df['estado'] == estado), 'le_escreve_percentual(%)'].values[0]]
                fundamental_incompleto = [df.loc[(df['estado'] == estado), 
                    'fundamental_incompleto_percentual(%)'].values[0]]
                fundamental_completo = [df.loc[(df['estado'] == estado), 
                    'fundamental_completo_percentual(%)'].values[0]]
                medio_incompleto = [df.loc[(df['estado'] == estado), 'medio_incompleto_percentual(%)'].values[0]]
                medio_completo = [df.loc[(df['estado'] == estado), 
                    'medio_completo_percentual(%)'].values[0]]
                superior_incompleto = [df.loc[(df['estado'] == estado), 
                    'superior_incompleto_percentual(%)'].values[0]]
                superior_completo = [df.loc[(df['estado'] == estado), 
                    'superior_completo_percentual(%)'].values[0]]

                my_layout = Layout(hoverlabel=dict(
                    bgcolor='#FFFFFF'), template='simple_white')

                fig = go.Figure(data=[
                    go.Bar(name='', x=nomeEstado, y=analfabeto,
                        hovertemplate='Analfabeto: {}%'.format(
                        str(analfabeto[0]).replace('.', ',')), marker_color='#355070', showlegend=False),
                    go.Bar(name='', x=nomeEstado, y=le_escreve,
                        hovertemplate='Lê e escreve: {}%'.format(
                    str(le_escreve[0]).replace('.', ',')), marker_color='#597092', showlegend=False),
                    go.Bar(name='', x=nomeEstado, y=fundamental_incompleto,
                        hovertemplate='Fundamental incompleto: {}%'.format(
                    str(fundamental_incompleto[0]).replace('.', ',')), marker_color='#7179E6', showlegend=False),
                    go.Bar(name='', x=nomeEstado, y=fundamental_completo,
                        hovertemplate='Fundamental completo: {}%'.format(
                    str(fundamental_completo[0]).replace('.', ',')), marker_color='#DEE0FC', showlegend=False),
                    go.Bar(name='', x=nomeEstado, y=medio_incompleto,
                        hovertemplate='Médio incompleto: {}%'.format(
                    str(medio_incompleto[0]).replace('.', ',')), marker_color='#E9DEFC', showlegend=False),
                    go.Bar(name='', x=nomeEstado, y=medio_completo,
                        hovertemplate='Médio completo: {}%'.format(
                    str(medio_completo[0]).replace('.', ',')), marker_color='#FEE592', showlegend=False),
                    go.Bar(name='', x=nomeEstado, y=superior_incompleto,
                        hovertemplate='Superior incompleto: {}%'.format(
                    str(superior_incompleto[0]).replace('.', ',')), marker_color='#E6DD39', showlegend=False),
                    go.Bar(name='', x=nomeEstado, y=superior_completo,
                        hovertemplate='Superior completo: {}%'.format(
                    str(superior_completo[0]).replace('.', ',')), marker_color='#FCC202', showlegend=False)
                ], layout=my_layout)

                fig.update_layout(
                    barmode='stack',
                    bargap=0, bargroupgap=0,
                    margin=dict(l=1, r=1, t=1, b=1),
                    yaxis_range=[0, 100],
                    yaxis=dict(
                        tickvals=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                        ticktext=['0%', '10%', '20%', '30%', '40%', '50%',
                                '60%', '70%', '80%', '90%', '100%']
                    )
                )

                fig.update_traces(width=0.5)
                fig.update_xaxes(ticksuffix="")
                fig.update_yaxes(ticksuffix="")
                st.plotly_chart(fig, use_container_width=True)

            plot_chart(estado, df)

    st.write('Estados com mais eleitores analfabetos')
    Q7, Q8 = st.columns(2)

    with Q7:
        top_10_analfabetos = df[['estado', 'analfabeto']].sort_values(
            by='analfabeto', ascending=False)[:10]

        x1 = top_10_analfabetos['estado']
        analfabeto = top_10_analfabetos['analfabeto']

        colors = ['#FCC202', '#E6DD39', '#FEE592', '#FEE592', '#E1E0C7',
                  '#DEE0FC', '#A6ACE6', '#7179E6', '#597092', '#355070']

        my_layout = Layout(hoverlabel=dict(
            bgcolor='#FFFFFF'), template='simple_white')

        fig_analfabetos = go.Figure(data=[
            go.Bar(name='', x=x1, y=analfabeto, hovertemplate=' ',
                   text=analfabeto, 
                   textposition='outside',
                   marker_color=colors, showlegend=False)],
            layout=my_layout)
        if (dados == 'Estadual - 1º turno'):
            fig_analfabetos.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis_range=[0, 850000],
                yaxis=dict(
                    tickvals=[0, 100000, 200000, 300000, 400000,
                              500000, 600000, 700000, 800000, ],
                    ticktext=['0', '100 mil', '200 mil', '300 mil', '400 mil', '500 mil', '600 mil', '700 mil', '800 mil'])
            )
        else:
            fig_analfabetos.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis_range=[0, 300000],
                yaxis=dict(
                    tickvals=[0, 50000, 100000, 150000,
                              200000, 250000, 300000],
                    ticktext=['0', '50 mil', '100 mil', '150 mil',
                              '200 mil', '250 mil', '300 mil'])
            )

        st.plotly_chart(fig_analfabetos, use_container_width=True)

    with Q8:
        def plot_chart(estadoIndex, df):
            estado = format_func_estado(estadoIndex)
            valor = df.loc[(df['estado'] == estado), 'analfabeto'].values[0]
            
            fig = go.Figure(
                go.Indicator(
                    value=valor,
                    title={'text': f"Número de eleitores analfabetos em {estado}"},
                    number={'font_color': '#355070',
                            'font_size': 80, "valueformat": ".0f"},
                    align='center'))

            st.plotly_chart(fig, use_container_width=True)

        plot_chart(estado, df)
    
    st.write('Estados com maior percentual de eleitores analfabetos')
    Q9, Q10 = st.columns(2)
    with Q9:
        top_10_analfabetos_percentual = df[['estado', 'analfabeto_percentual(%)']].sort_values(
            by='analfabeto_percentual(%)', ascending=False)[:10]

        x1 = top_10_analfabetos_percentual['analfabeto_percentual(%)']
        analfabeto = top_10_analfabetos_percentual['estado']

        colors = ['#FCC202', '#E6DD39', '#FEE592', '#FEE592', '#E1E0C7',
                '#DEE0FC', '#A6ACE6', '#7179E6', '#597092', '#355070']

        my_layout = Layout(hoverlabel=dict(
            bgcolor='#FFFFFF'), template='simple_white')

        fig_percentual_analfabetos = go.Figure(data=[
            go.Bar(name='', x=x1, y=analfabeto, 
                hovertemplate=[f"{percent:.2f}%" for percent in x1],
                text=[f"{percent:.2f}%" for percent in x1], 
                textposition='outside', 
                marker_color=colors, showlegend=False,
                orientation='h',)], layout=my_layout)

        fig_percentual_analfabetos.update_layout(
            xaxis_range=[0, 100]
        )

        fig_percentual_analfabetos.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                tickvals=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                ticktext=['0%', '10%', '20%', '30%', '40%', '50%', 
                    '60%', '70%', '80%', '90%', '100%']),
            yaxis=dict(showgrid=False, zeroline=False, autorange="reversed"))

        st.plotly_chart(fig_percentual_analfabetos, use_container_width=True)
    with Q10:
        def plot_chart(estadoIndex, df):
            estado = format_func_estado(estadoIndex)
            valor = df.loc[(df['estado'] == estado), 'analfabeto_percentual(%)'].values[0]
            
            fig = go.Figure(
                go.Indicator(
                    value=valor,
                    title={'text': f"Percentual de eleitores analfabetos em {estado}"},
                    number={'font_color': '#355070', 'suffix':'%',
                            'font_size': 80, "valueformat": ".2f"},
                    align='center'))

            st.plotly_chart(fig, use_container_width=True)

        plot_chart(estado, df)
    
    st.write('Estados com mais eleitores com deficiência')
    Q11, Q12 = st.columns(2)

    with Q11:
        top_10_deficiencia = df[['estado', 'eleitores_deficiencia']].sort_values(
            by='eleitores_deficiencia', ascending=False)[:10].reset_index()

        colors = ['#FCC202', '#E6DD39', '#FEE592', '#FEE592', '#E1E0C7',
                  '#DEE0FC', '#A6ACE6', '#7179E6', '#597092', '#355070']

        my_layout = Layout(hoverlabel=dict(
            bgcolor='#FFFFFF'), template='simple_white')

        fig_deficientes = go.Figure()
        fig_deficientes.update_xaxes(title_text=' ')
        fig_deficientes.update_yaxes(title_text=' ')
        fig_deficientes.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showline=True,
                showgrid=False,
                zeroline=False,
            ),
            yaxis=dict(
                mirror=False,
                showline=True,
                showgrid=False,
                zeroline=False,
                tickvals=[0, 50000, 100000, 150000, 200000,
                          250000, 300000, 350000, 400000, 450000],
                ticktext=['0', '50 mil', '100 mil', '150 mil',
                          '200 mil', '250 mil', '300 mil', '350 mil', '400 mil', '450 mil']
            ))

        # pontos
        fig_deficientes.add_trace(
            go.Scatter(
                x=top_10_deficiencia["estado"],
                y=top_10_deficiencia["eleitores_deficiencia"],
                mode='markers+text',
                name='',
                text=top_10_deficiencia["eleitores_deficiencia"],
                textposition='top center',
                hovertemplate='%{y}',
                marker_color=colors,
                marker_size=25))
        # linhas
        for i, v in top_10_deficiencia["eleitores_deficiencia"].items():
            fig_deficientes.add_shape(
                type='line',
                x0=i, y0=0,
                x1=i,
                y1=v,
                line=dict(color=colors[i], width=10))

        st.plotly_chart(fig_deficientes, use_container_width=True)

    with Q12:
        def plot_chart(estadoIndex, df):
            estado = format_func_estado(estadoIndex)
            valor = df.loc[(df['estado'] == estado), 'eleitores_deficiencia'].values[0]
            
            fig = go.Figure(
                go.Indicator(
                    value=valor,
                    title={'text': f"Número de eleitores com deficiência em {estado}"},
                    number={'font_color': '#355070', 
                            'font_size': 80, "valueformat": ".0f"},
                    align='center'))

            st.plotly_chart(fig, use_container_width=True)

        plot_chart(estado, df)

    st.write('Estados com maior percentual de eleitores com deficiência')
    Q13, Q14 = st.columns(2)

    with Q13:
        top_10_deficiencia_percentual = df[['estado', 'eleitores_deficiencia_percentual(%)']].sort_values(
            by='eleitores_deficiencia_percentual(%)', ascending=False)[:10].reset_index()

        fig_percentual_deficientes = go.Figure()
        fig_percentual_deficientes.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_range=[0, 100],
            xaxis=dict(
                ticks="outside",
                mirror=False,
                showline=True,
                showgrid=False,
                zeroline=False,
                tickvals=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                ticktext=['0%', '10%', '20%', '30%', '40%', '50%',
                        '60%', '70%', '80%', '90%', '100%']),
            yaxis=dict(
                ticks="outside",
                mirror=False,
                showline=True,
                showgrid=False,
                zeroline=False,
                autorange="reversed"))

        # pontos
        fig_percentual_deficientes.add_trace(
            go.Scatter(
                x=top_10_deficiencia_percentual["eleitores_deficiencia_percentual(%)"],
                y=top_10_deficiencia_percentual["estado"],
                mode='markers+text',
                name='',
                text=[f"{percent:.2f}%" for percent in top_10_deficiencia_percentual["eleitores_deficiencia_percentual(%)"]],
                textposition='middle right',
                hovertemplate=[
                    f"{percent:.2f}%" for percent in top_10_deficiencia_percentual['eleitores_deficiencia_percentual(%)']],
                marker_color=colors,
                marker_size=20))
        # linhas
        for i, v in top_10_deficiencia_percentual['eleitores_deficiencia_percentual(%)'].items():
            fig_percentual_deficientes.add_shape(
                type='line',
                x0=0, y0=i,
                x1=v,
                y1=i,
                line=dict(color=colors[i], width=8))

        st.plotly_chart(fig_percentual_deficientes, use_container_width=True)

    with Q14:
        def plot_chart(estadoIndex, df):
            estado = format_func_estado(estadoIndex)
            valor = df.loc[(df['estado'] == estado), 'eleitores_deficiencia_percentual(%)'].values[0]
            
            fig = go.Figure(
                go.Indicator(
                    value=valor,
                    title={'text': f"Percentual de eleitores com deficiência em {estado}"},
                    number={'font_color': '#355070', 'suffix': '%', 
                            'font_size': 80, "valueformat": ".2f"},
                    align='center'))

            st.plotly_chart(fig, use_container_width=True)

        plot_chart(estado, df)
        # st.write('Estados com maior percentual de eleitores com deficiência')
        # 

    st.write('Eleitorado facultativo por estado')

    with st.empty():
        facultativos = df[['estado', 'eleitorado_facultativo_percentual(%)', '16_anos_percentual(%)', '17_anos_percentual(%)',
                           '65_69_anos_percentual(%)', '70_74_anos_percentual(%)', '75_79_anos_percentual(%)',
                           '80_84_anos_percentual(%)', '85_89_anos_percentual(%)', '90_94_anos_percentual(%)',
                           '95_99_anos_percentual(%)', '100_anos_percentual(%)']].sort_values(by='eleitorado_facultativo_percentual(%)', ascending=False)

        jovens = facultativos['16_anos_percentual(%)'] + \
            facultativos['17_anos_percentual(%)']
        idosos = facultativos['65_69_anos_percentual(%)'] + facultativos['70_74_anos_percentual(%)'] + facultativos['75_79_anos_percentual(%)'] + facultativos['80_84_anos_percentual(%)'] + \
            facultativos['85_89_anos_percentual(%)'] + facultativos['90_94_anos_percentual(%)'] + \
            facultativos['95_99_anos_percentual(%)'] + \
            facultativos['100_anos_percentual(%)']

        colors = ['#FCC202', '#355070']

        df = facultativos
        df['jovens'] = jovens
        df['idosos'] = idosos
        df['total'] = jovens + idosos

        my_layout = Layout(hoverlabel=dict(
            bgcolor='#FFFFFF'), template='simple_white')

        fig_facultativo = go.Figure(layout=my_layout)

        fig_facultativo.add_trace(go.Scatter(
            x=facultativos['estado'],
            y=df['idosos'],
            hovertemplate=[f"{percent:.2f}%" for percent in df['idosos']],
            marker=dict(color="#FCC202"),
            name='Idosos',
            showlegend=True))

        fig_facultativo.add_trace(go.Scatter(
            x=df['estado'],
            y=df['jovens'],
            hovertemplate=[f"{percent:.2f}%" for percent in df['jovens']],
            marker=dict(color="#355070"),
            name='Jovens',
            showlegend=True))

        fig_facultativo.add_trace(go.Scatter(
            x=facultativos['estado'],
            y=df['total'],
            hovertemplate=[f"{percent:.2f}%" for percent in df['total']],
            marker=dict(color="#296B21"),
            name='Total',
            showlegend=True))

        fig_facultativo.update_layout(hovermode="x unified", yaxis_range=[0, 100], plot_bgcolor='rgba(255,255,255,255)',
                                      xaxis=dict(showgrid=False,
                                                 zeroline=False),
                                      yaxis=dict(showgrid=False,
                                                 zeroline=False,
                                                 tickvals=[
                                                     0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                                                 ticktext=['0%', '10%', '20%', '30%', '40%',
                                                           '50%', '60%', '70%', '80%', '90%', '100%']),
                                      xaxis_title="",
                                      yaxis_title="",
                                      legend_title='Legenda',)

        st.plotly_chart(fig_facultativo, use_container_width=True)
else:
    ESTADOS = (df['estado'].drop_duplicates())

    def format_func_estado(option):
        return ESTADOS[option]

    estado = st.selectbox(
        "", options=list(ESTADOS.keys()), 
        format_func=format_func_estado,
        key='estadosAnalfabetismoPercentualMunicipal')
    municipios = list(df.loc[df['estado'] == str(
        format_func_estado(estado)), 'municipio'])

    indexMunicipio = st.selectbox(
        "",
        range(len(municipios)),
        format_func=lambda x: municipios[x],
        key='analfabetismoPercentualMunicipal')
    
    with st.empty():
            Q30, Q31, Q32 = st.columns(3)
            with Q30:
                st.write(' ')

            with Q31:
                def plot_chart(estadoIndex, municipios, index, df):
                    estado = format_func_estado(estadoIndex)
                    cidade = municipios[indexMunicipio]
                    valor = df.loc[(df['estado'] == estado)
                            & (df['municipio'] == cidade), 'comparecimento_percentual(%)'].values[0]
                    # st.markdown(f"<h1 style='text-align: center; color: grey; font-size:40px'>Comparecimento percentual em {cidade}</h1>", unsafe_allow_html=True)
                    # st.markdown(f"<h1 style='text-align: center; color: #355070; font-size:60px; font-family:Times New Roman'>1208 {valor}%</h1>", unsafe_allow_html=True)
                    fig = go.Figure(
                        go.Indicator(
                            value=valor,
                            title={'text': f"Comparecimento percentual de eleitores em {cidade}"},
                            number={'font_color': '#355070', "suffix": "%",
                                    'font_size': 40, "valueformat": ".2f"},
                            align='center'))
                    #fig.update_layout(
                        # autosize=False,
                    #     width=20,
                    #     height=20
                    # )

                    st.plotly_chart(fig, use_container_width=False)

                plot_chart(estado, municipios, indexMunicipio, df)

            with Q32:
                st.write('fjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\nfjklfd\n')
    # M U N I C Í P I O S
    st.write('Comparecimento percentual por município')
    if (dados == 'Municipal - 1º turno'):
        Q1, Q2, Q3 = st.columns(3)

        with Q1:
            htmlFile = open(
                "D:\\UFMS\\TCC\\Dashboard\\data\\charts\\municipios_1turno\\mapa1_municipios_1turno.html", 'r', encoding='utf-8')
            source_code = htmlFile.read()
            components.html(source_code, height=480)

        with Q2:
            htmlFile = open(
                "D:\\UFMS\\TCC\\Dashboard\\data\\charts\\municipios_1turno\\mapa2_municipios_1turno.html", 'r', encoding='utf-8')
            source_code = htmlFile.read()
            components.html(source_code, height=480)

        with Q3:
            htmlFile = open(
                "D:\\UFMS\\TCC\\Dashboard\\data\\charts\\municipios_1turno\\mapa3_municipios_1turno.html", 'r', encoding='utf-8')
            source_code = htmlFile.read()
            components.html(source_code, height=480)

    else:
        with st.empty():
            htmlFile = open(
                "D:\\UFMS\\TCC\\Dashboard\\data\\charts\\municipios_2turno\\mapa_municipios_2turno.html", 'r', encoding='utf-8')
            source_code = htmlFile.read()
            components.html(source_code, height=480)
    
    Q4, Q5 = st.columns(2)

    with Q4:
        st.write('Divisão de sexos por município')

        def plot_chart(estadoIndex, municipios, index, df):
            estado = format_func_estado(estadoIndex)
            cidade = [municipios[index]]

            homens = [df.loc[(df['estado'] == estado)
                & (df['municipio'] == cidade[0]), 
                'eleitorado_masculino_percentual(%)'].values[0]]
            
            mulheres = [df.loc[(df['estado'] == estado)
                & (df['municipio'] == cidade[0]), 
                'eleitorado_feminino_percentual(%)'].values[0]]

            my_layout = Layout(hoverlabel=dict(
                bgcolor='#FFFFFF'), template='simple_white')

            fig_sexoMunicipio = go.Figure()
            fig_sexoMunicipio.add_trace(go.Bar(y=cidade, x=homens,
                                               name='',
                                               hovertemplate='Homens: %{x:.2f}%',
                                               marker_color='#355070',
                                               orientation='h'))

            fig_sexoMunicipio.add_trace(go.Bar(y=cidade, x=mulheres,
                                               hovertemplate='Mulheres: %{x:.2f}%',
                                               marker_color='#FCC202',
                                               name='',
                                               orientation='h'))

            fig_sexoMunicipio.update_layout(barmode='relative',
                                            hoverlabel=dict(bgcolor='#FFFFFF'),
                                            template='simple_white',
                                            bargap=0, bargroupgap=0,
                                            margin=dict(l=1, r=1, t=60, b=1),
                                            xaxis_range=[0, 100],
                                            xaxis=dict(
                                                tickvals=[0, 10, 20, 30, 40,
                                                          50, 60, 70, 80, 90, 100],
                                                ticktext=['0%', '10%', '20%', '30%', '40%', '50%',
                                                          '60%', '70%', '80%', '90%', '100%']))

            fig_sexoMunicipio.update_traces(width=0.5)
            fig_sexoMunicipio.update_xaxes(ticksuffix="")
            fig_sexoMunicipio.update_yaxes(ticksuffix="")
            st.plotly_chart(fig_sexoMunicipio, use_container_width=True)

        plot_chart(estado, municipios, indexMunicipio, df)

    with Q5:
        #ESCOLARIDADE POR MUNICÍPIO
        st.write('Divisão por escolaridade por município')

        def plot_chart(estadoIndex, municipios, index, df):

            estado = format_func_estado(estadoIndex)
            cidade = [municipios[index]]
            analfabeto = [df.loc[(df['estado'] == estado)
                           & (df['municipio'] == cidade[0]), 'analfabeto_percentual(%)'].values[0]]
            le_escreve = [df.loc[(df['estado'] == estado)
                           & (df['municipio'] == cidade[0]), 'le_escreve_percentual(%)'].values[0]]
            fundamental_incompleto = [df.loc[(df['estado'] == estado)
                & (df['municipio'] == cidade[0]), 
                'fundamental_incompleto_percentual(%)'].values[0]]
            fundamental_completo = [df.loc[(df['estado'] == estado)
                & (df['municipio'] == cidade[0]), 
                'fundamental_completo_percentual(%)'].values[0]]
            medio_incompleto = [df.loc[(df['estado'] == estado)
                & (df['municipio'] == cidade[0]), 'medio_incompleto_percentual(%)'].values[0]]
            medio_completo = [df.loc[(df['estado'] == estado)
                & (df['municipio'] == cidade[0]), 
                'medio_completo_percentual(%)'].values[0]]
            superior_incompleto = [df.loc[(df['estado'] == estado)
                & (df['municipio'] == cidade[0]), 
                'superior_incompleto_percentual(%)'].values[0]]
            superior_completo = [df.loc[(df['estado'] == estado)
                & (df['municipio'] == cidade[0]), 
                'superior_completo_percentual(%)'].values[0]]

            my_layout = Layout(hoverlabel=dict(
                bgcolor='#FFFFFF'), template='simple_white')

            fig = go.Figure(data=[
                go.Bar(name='', x=cidade, y=analfabeto,
                       hovertemplate='Analfabeto: {}%'.format(
                       str(analfabeto[0]).replace('.', ',')), marker_color='#355070', showlegend=False),
                go.Bar(name='', x=cidade, y=le_escreve,
                       hovertemplate='Lê e escreve: {}%'.format(
                str(le_escreve[0]).replace('.', ',')), marker_color='#597092', showlegend=False),
                go.Bar(name='', x=cidade, y=fundamental_incompleto,
                       hovertemplate='Fundamental incompleto: {}%'.format(
                str(fundamental_incompleto[0]).replace('.', ',')), marker_color='#7179E6', showlegend=False),
                go.Bar(name='', x=cidade, y=fundamental_completo,
                       hovertemplate='Fundamental completo: {}%'.format(
                str(fundamental_completo[0]).replace('.', ',')), marker_color='#DEE0FC', showlegend=False),
                go.Bar(name='', x=cidade, y=medio_incompleto,
                       hovertemplate='Médio incompleto: {}%'.format(
                str(medio_incompleto[0]).replace('.', ',')), marker_color='#E9DEFC', showlegend=False),
                go.Bar(name='', x=cidade, y=medio_completo,
                       hovertemplate='Médio completo: {}%'.format(
                str(medio_completo[0]).replace('.', ',')), marker_color='#FEE592', showlegend=False),
                go.Bar(name='', x=cidade, y=superior_incompleto,
                       hovertemplate='Superior incompleto: {}%'.format(
                str(superior_incompleto[0]).replace('.', ',')), marker_color='#E6DD39', showlegend=False),
                go.Bar(name='', x=cidade, y=superior_completo,
                       hovertemplate='Superior completo: {}%'.format(
                str(superior_completo[0]).replace('.', ',')), marker_color='#FCC202', showlegend=False)
            ], layout=my_layout)

            fig.update_layout(
                barmode='stack',
                bargap=0, bargroupgap=0,
                margin=dict(l=1, r=1, t=1, b=1),
                yaxis_range=[0, 100],
                yaxis=dict(
                    tickvals=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                    ticktext=['0%', '10%', '20%', '30%', '40%', '50%',
                              '60%', '70%', '80%', '90%', '100%']
                )
            )

            fig.update_traces(width=0.5)
            fig.update_xaxes(ticksuffix="")
            fig.update_yaxes(ticksuffix="")
            st.plotly_chart(fig, use_container_width=True)

        plot_chart(estado, municipios, indexMunicipio, df)

    Q6, Q7 = st.columns(2)
    with Q6:
        st.write('Municípios com mais eleitores analfabetos')
        top_10_analfabetos = df[['municipio', 'analfabeto']].sort_values(
            by='analfabeto', ascending=False)[:10]

        x1 = top_10_analfabetos['municipio']
        analfabeto = top_10_analfabetos['analfabeto']

        colors = ['#FCC202', '#E6DD39', '#FEE592', '#FEE592', '#E1E0C7',
                  '#DEE0FC', '#A6ACE6', '#7179E6', '#597092', '#355070']

        my_layout = Layout(hoverlabel=dict(
            bgcolor='#FFFFFF'), template='simple_white')

        fig_analfabetos = go.Figure(data=[
            go.Bar(name='', x=x1, y=analfabeto, hovertemplate=' ',
                   text=analfabeto, textposition='outside',
                   marker_color=colors, showlegend=False)],
            layout=my_layout)
        if (dados == 'Municipal - 1º turno'):
            fig_analfabetos.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis_range=[0, 200000],
                yaxis=dict(
                    tickvals=[0, 50000, 100000, 150000, 200000],
                    ticktext=['0', '50 mil', '100 mil', '150 mil', '200 mil'])
            )
        elif (dados == 'Municipal - 2º turno'):
            fig_analfabetos.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis_range=[0, 200000],
                yaxis=dict(
                    tickvals=[0, 50000, 100000, 150000,
                              200000, 250000, 300000],
                    ticktext=['0', '50 mil', '100 mil', '150 mil',
                              '200 mil', '250 mil', '300 mil'])
            )

        st.plotly_chart(fig_analfabetos, use_container_width=True)

    with Q7:
        def plot_chart(estadoIndex, municipios, index, df):
            estado = format_func_estado(estadoIndex)
            cidade = municipios[index]

            valor = df.loc[(df['estado'] == estado)
                           & (df['municipio'] == cidade), 'analfabeto'].values[0]
            fig = go.Figure(
                go.Indicator(
                    value=valor,
                    title={'text': f"Número de eleitores analfabetos em {cidade}"},
                    number={'font_color': '#355070',
                            'font_size': 80, "valueformat": ".0f"},
                    align='center'))

            st.plotly_chart(fig, use_container_width=True)

        plot_chart(estado, municipios, indexMunicipio, df)
    
    Q8, Q9 = st.columns(2)
    with Q8:
        st.write('Municípios com maior percentual de eleitores analfabetos')
        top_10_analfabetos = df[['municipio', 'analfabeto_percentual(%)']].sort_values(
            by='analfabeto_percentual(%)', ascending=False)[:10]

        x1 = top_10_analfabetos['municipio']
        analfabeto = top_10_analfabetos['analfabeto_percentual(%)']

        colors = ['#FCC202', '#E6DD39', '#FEE592', '#FEE592', '#E1E0C7',
                  '#DEE0FC', '#A6ACE6', '#7179E6', '#597092', '#355070']

        my_layout = Layout(hoverlabel=dict(
            bgcolor='#FFFFFF'), template='simple_white')

        fig_analfabetos_percentual = go.Figure(data=[
            go.Bar(name='', x=analfabeto, y=x1, hovertemplate=' ',
                   text=[f"{percent:.2f}%" for percent in analfabeto], textposition='outside',
                   marker_color=colors, showlegend=False, orientation='h')],
            layout=my_layout)
        fig_analfabetos_percentual.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(autorange="reversed"),
                xaxis_range=[0, 100],
                xaxis=dict(
                    tickvals=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                    ticktext=['0%', '10%', '20%', '30%', '40%', '50%',
                    '60%', '70%', '80%', '90%', '100%'])
            )
        st.plotly_chart(fig_analfabetos_percentual, use_container_width=True)

    with Q9:
        #ANALFABETISMO PERCENTUAL MUNICIPAL
        def plot_chart(estadoIndex, municipios, index, df):
            estado = format_func_estado(estadoIndex)
            cidade = municipios[index]

            valor = df.loc[(df['estado'] == estado)
                           & (df['municipio'] == cidade), 'analfabeto_percentual(%)'].values[0]
            fig = go.Figure(
                go.Indicator(
                    value=valor,
                    title={'text': f"Percentual de eleitores analfabetos em {cidade}"},
                    number={'font_color': '#355070', "suffix": "%",
                            'font_size': 80, "valueformat": ".2f"},
                    align='center'))

            st.plotly_chart(fig, use_container_width=True)

        plot_chart(estado, municipios, indexMunicipio, df)

    Q10, Q11 = st.columns(2)
    with Q10:
        #ELEITORADO COM DEFICIÊNCIA
        st.write('Municípios com mais eleitores com deficiência')
        top_10_deficiencia = df[['municipio', 'eleitores_deficiencia']].drop_duplicates().sort_values(by = 'eleitores_deficiencia', ascending = False)[:10].reset_index()

        colors = ['#FCC202', '#E6DD39', '#FEE592', '#FEE592', '#E1E0C7', '#DEE0FC', '#A6ACE6', '#7179E6', '#597092', '#355070']

        my_layout = Layout(hoverlabel = dict(bgcolor = '#FFFFFF'), template='simple_white')

        fig_deficientes = go.Figure()
        fig_deficientes.update_xaxes(title_text=' ')
        fig_deficientes.update_yaxes(title_text=' ')
        fig_deficientes.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                mirror=False,
                showline=True,
                showgrid=False,
                zeroline=False,),
            yaxis=dict(
                showgrid=False, 
                zeroline=False,
                mirror=False,
                showline=True,
                tickvals = [0, 50000, 100000, 150000, 200000],
                ticktext = ['0', '50 mil', '100 mil', '150 mil', '200 mil']
            ))

        # pontos
        fig_deficientes.add_trace(
            go.Scatter(
                x = top_10_deficiencia["municipio"],
                y = top_10_deficiencia["eleitores_deficiencia"], 
                mode = 'markers+text',
                name='',
                text=top_10_deficiencia["eleitores_deficiencia"],
                textposition='top center',
                hovertemplate = '%{y}',
                marker_color =colors,
                marker_size  = 25))
        # linhas
        for i, v in top_10_deficiencia["eleitores_deficiencia"].items():
            fig_deficientes.add_shape(
                type='line',
                x0 = i, y0 = 0,
                x1 = i,
                y1 = v,
                line=dict(color=colors[i], width = 10))
        if (dados == 'Municipal - 1º turno'):
            fig_deficientes.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis_range=[0, 200000],
            yaxis=dict(
                tickvals=[0, 25000, 50000, 75000, 
                100000, 125000, 150000, 175000, 200000],
                ticktext=['0', '25 mil', '50 mil', '75 mil', 
                '100 mil', '125 mil', '150 mil', '175 mil', '200 mil'])
            )
        elif (dados == 'Municipal - 2º turno'):
            fig_deficientes.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis_range=[0, 200000],
                yaxis=dict(
                    tickvals=[0, 50000, 100000, 150000,
                        200000, 250000, 300000],
                    ticktext=['0', '50 mil', '100 mil', '150 mil',
                        '200 mil', '250 mil', '300 mil'])
            )

        st.plotly_chart(fig_deficientes, use_container_width=True)

    with Q11:
        #ELEITORADO MUNICIPAL COM DEFICIÊNCIA
        def plot_chart(estadoIndex, municipios, index, df):
            estado = format_func_estado(estadoIndex)
            cidade = municipios[index]

            valor = df.loc[(df['estado'] == estado)
                           & (df['municipio'] == cidade), 'eleitores_deficiencia'].values[0]
            fig = go.Figure(
                go.Indicator(
                    value=valor,
                    title={'text': f"Número de eleitores com deficiência em {cidade}"},
                    number={'font_color': '#355070',
                            'font_size': 80, "valueformat": ".0f"},
                    align='center'))

            st.plotly_chart(fig, use_container_width=True)

        plot_chart(estado, municipios, indexMunicipio, df)

    Q12, Q13 = st.columns(2)
    with Q12:
        st.write('Municípios com maior percentual de eleitores com deficiência')
        top_10_deficiencia_percentual = df[['municipio', 'eleitores_deficiencia_percentual(%)']].sort_values(
            by='eleitores_deficiencia_percentual(%)', ascending=False)[:10].reset_index()

        fig_percentual_deficientes = go.Figure()
        fig_percentual_deficientes.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_range=[0, 100],
            xaxis=dict(
                ticks="outside",
                mirror=False,
                showline=True,
                showgrid=False,
                zeroline=False,
                tickvals=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                ticktext=['0%', '10%', '20%', '30%', '40%', '50%',
                '60%', '70%', '80%', '90%', '100%']),
            yaxis=dict(
                ticks="outside",
                mirror=False,
                showline=True,
                showgrid=False,
                zeroline=False,
                autorange="reversed"))

        # pontos
        fig_percentual_deficientes.add_trace(
            go.Scatter(
                x=top_10_deficiencia_percentual["eleitores_deficiencia_percentual(%)"],
                y=top_10_deficiencia_percentual["municipio"],
                mode='markers+text',
                name='',
                text=[f"{percent:.2f}%" for percent in top_10_deficiencia_percentual["eleitores_deficiencia_percentual(%)"]],
                textposition='middle right',
                hovertemplate=[
                    f"{percent:.2f}%" for percent in top_10_deficiencia_percentual['eleitores_deficiencia_percentual(%)']],
                marker_color=colors,
                marker_size=20))
        # linhas
        for i, v in top_10_deficiencia_percentual['eleitores_deficiencia_percentual(%)'].items():
            fig_percentual_deficientes.add_shape(
                type='line',
                x0=0, y0=i,
                x1=v,
                y1=i,
                line=dict(color=colors[i], width=8))

        st.plotly_chart(fig_percentual_deficientes, use_container_width=True)

    with Q13:
        def plot_chart(estadoIndex, municipios, index, df):
            estado = format_func_estado(estadoIndex)
            cidade = municipios[index]

            valor = df.loc[(df['estado'] == estado)
                           & (df['municipio'] == cidade), 'eleitores_deficiencia_percentual(%)'].values[0]
            fig = go.Figure(
                go.Indicator(
                    value=valor,
                    title={'text': f"Percentual de eleitores com deficiência em {cidade}"},
                    number={'font_color': '#355070', "suffix": "%",
                            'font_size': 80, "valueformat": ".2f"},
                    align='center'))

            st.plotly_chart(fig, use_container_width=True)

        plot_chart(estado, municipios, indexMunicipio, df)

    Q14, Q15 = st.columns(2)

    facultativos = df[['estado', 'municipio', 'eleitorado_facultativo_percentual(%)','16_anos_percentual(%)', '17_anos_percentual(%)', 
      '65_69_anos_percentual(%)', '70_74_anos_percentual(%)', '75_79_anos_percentual(%)',
       '80_84_anos_percentual(%)', '85_89_anos_percentual(%)', '90_94_anos_percentual(%)',
       '95_99_anos_percentual(%)', '100_anos_percentual(%)']].sort_values(by = 'eleitorado_facultativo_percentual(%)', ascending = False)
    
    with Q14:
        st.write('Municípios com maior eleitorado facultativo')
        jovens = facultativos['16_anos_percentual(%)'] + facultativos['17_anos_percentual(%)']
        idosos = facultativos['65_69_anos_percentual(%)'] + facultativos['70_74_anos_percentual(%)'] + facultativos['75_79_anos_percentual(%)'] + facultativos['80_84_anos_percentual(%)'] + facultativos['85_89_anos_percentual(%)'] + facultativos['90_94_anos_percentual(%)'] + facultativos['95_99_anos_percentual(%)'] + facultativos['100_anos_percentual(%)']

        colors = ['#FCC202', '#355070']

        facultativos['jovens'] = jovens
        facultativos['idosos'] = idosos
        facultativos['total'] = jovens + idosos

        my_layout = Layout(hoverlabel = dict(bgcolor = '#FFFFFF'), template='simple_white')

        fig_facultativo = go.Figure(layout=my_layout)

        fig_facultativo.add_trace(go.Scatter(
            x = facultativos['municipio'][:10],
            y = facultativos['idosos'][:10],
            hovertemplate = [f"{percent:.2f}%" for percent in facultativos['idosos']],
            marker=dict(color="#FCC202"),
            name='Idosos',
            showlegend = True))

        fig_facultativo.add_trace(go.Scatter(
            x = facultativos['municipio'][:10],
            y = facultativos['jovens'][:10],
            hovertemplate = [f"{percent:.2f}%" for percent in facultativos['jovens']],
            marker=dict(color="#355070"),
            name='Jovens',
            showlegend=True))

        fig_facultativo.add_trace(go.Scatter(
            x = facultativos['municipio'][:10],
            y = facultativos['total'][:10],
            hovertemplate = [f"{percent:.2f}%" for percent in facultativos['total']],
            marker=dict(color="#296B21"),
            name='Total',
            showlegend = True))

        fig_facultativo.update_layout(hovermode="x unified", yaxis_range=[0,100], plot_bgcolor='rgba(255,255,255,255)',
                        xaxis=dict(showgrid=False, 
                                    zeroline=False), 
                        yaxis=dict(showgrid=False, 
                                    zeroline=False,
                                    tickvals = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                                    ticktext = ['0%', '10%', '20%', '30%', '40%', 
                                    '50%', '60%', '70%', '80%', '90%', '100%']),
                        xaxis_title="",
                        yaxis_title="",
                        legend_title='Legenda',)

        st.plotly_chart(fig_facultativo, use_container_width=True)
    
    with Q15:
        def plot_chart(estadoIndex, municipios, index, df):
            estado = format_func_estado(estadoIndex)
            cidade = municipios[index]

            valor = facultativos.loc[(facultativos['estado'] == estado)
                & (facultativos['municipio'] == cidade), 'total'].values[0]
            fig = go.Figure(
                go.Indicator(
                    value=valor,
                    title={'text': f"Percentual do eleitorado facultativo em {cidade}"},
                    number={'font_color': '#355070', "suffix": "%",
                            'font_size': 80, "valueformat": ".2f"},
                    align='center'))

            st.plotly_chart(fig, use_container_width=True)

        plot_chart(estado, municipios, indexMunicipio, df)

    
