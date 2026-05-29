from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import models
from database import engine, SessaoLocal

# Cria o banco de dados
models.Base.metadata.create_all(bind=engine)

# Inicia a API (UMA ÚNICA VEZ)
app = FastAPI()

# O "CARIMBO DE AUTORIZAÇÃO" DO CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ficha de Triagem (Pydantic)
# Atualize a ficha para exigir o profissional
class FichaAgendamento(BaseModel):
    cliente_nome: str
    servico: str
    horario: str
    valor: float
    profissional: str # NOVO CAMPO AQUI

@app.post("/api/agendar")
def criar_agendamento(dados_recebidos: FichaAgendamento):
    db = SessaoLocal()
    novo_agendamento = models.Agendamento(
        cliente_nome=dados_recebidos.cliente_nome,
        servico=dados_recebidos.servico,
        horario=dados_recebidos.horario,
        valor=dados_recebidos.valor,
        profissional=dados_recebidos.profissional # SALVANDO NO BANCO
    )
    db.add(novo_agendamento)
    db.commit()
    db.close()
    return {"status": "Sucesso", "mensagem": f"Agendamento confirmado com {dados_recebidos.profissional}!"}

# Rota para LER do banco e filtrar horários
# Rota DINÂMICA SUPREMA CORRIGIDA: Trata colisões de intervalos reais de tempo
@app.get("/api/horarios/{duracao_minutos}/{profissional}")
def obter_horarios_fatiados(duracao_minutos: int, profissional: str):
    db = SessaoLocal()
    
    # 1. Puxa que horas a barbearia abre e fecha
    config = db.query(models.ConfiguracaoAgenda).first()
    abertura = 9  
    fechamento = 18
    if config is not None:
        abertura = config.hora_abertura
        fechamento = config.hora_fechamento

    # 2. Puxa os agendamentos do profissional escolhido
    agendamentos_do_barbeiro = db.query(models.Agendamento).filter(models.Agendamento.profissional == profissional).all()
    
    # 3. Monta o mapa de quais INTERVALOS de tempo este profissional está ocupado
    intervalos_ocupados = []
    for agendamento in agendamentos_do_barbeiro:
        # Busca no cardápio a duração do serviço que foi marcado para saber quando ele termina
        servico_cadastrado = db.query(models.ServicoBarbearia).filter(models.ServicoBarbearia.nome == agendamento.servico).first()
        duracao_ocupada = 30  # tempo padrão de segurança caso não encontre
        if servico_cadastrado is not None:
            duracao_ocupada = servico_cadastrado.duracao
            
        inicio_existente = datetime.strptime(agendamento.horario, "%H:%M")
        fim_existente = inicio_existente + timedelta(minutes=duracao_ocupada)
        
        # Guarda o bloco de tempo (Início, Fim) em que o barbeiro está trabalhando
        intervalos_ocupados.append((inicio_existente, fim_existente))
        
    db.close()

    # 4. Configura a grade de geração (de 30 em 30 minutos fixos para dar boas opções de início ao cliente)
    hora_atual = datetime.strptime(f"{abertura}:00", "%H:%M")
    hora_fim = datetime.strptime(f"{fechamento}:00", "%H:%M")
    # passo_grade = timedelta(minutes=30) # GRADE FIXA DE 30 MINUTOS
    passo_grade = timedelta(minutes=duracao_minutos)

    horarios_livres = []
    
    # 5. O loop testa se o serviço solicitado cabe em cada ponto da grade de tempo
    while (hora_atual + timedelta(minutes=duracao_minutos)) <= hora_fim:
        inicio_proposto = hora_atual
        fim_proposto = hora_atual + timedelta(minutes=duracao_minutos)
        
        # Varre os agendamentos do barbeiro procurando sobreposição de horários
        colisao = False
        for inicio_existente, fim_existente in intervalos_ocupados:
            # Fórmula matemática de intersecção de intervalos (Janelas sobrepostas)
            if max(inicio_proposto, inicio_existente) < min(fim_proposto, fim_existente):
                colisao = True
                break
        
        # Se nenhuma colisão aconteceu, significa que o profissional está 100% livre nesse bloco!
        if not colisao:
            horarios_livres.append(hora_atual.strftime("%H:%M"))
            
        hora_atual += passo_grade

    return {"horarios_disponiveis": horarios_livres}


    #-----------#

    # Rota exclusiva para o Painel do Barbeiro (Admin)
@app.get("/api/agendamentos")
def listar_todos_agendamentos():
    db = SessaoLocal()
    # Puxa literalmente todas as linhas da tabela no banco de dados
    todos_os_agendamentos = db.query(models.Agendamento).all()
    db.close()
    
    # O FastAPI é inteligente o suficiente para transformar essa lista
    # de objetos do banco diretamente em um JSON para o nosso frontend!
    return todos_os_agendamentos

    #-------------------#

    # Rota para DELETAR um agendamento específico
@app.delete("/api/agendamentos/{agendamento_id}")
def cancelar_agendamento(agendamento_id: int):
    db = SessaoLocal()
    
    # 1. Procura no banco de dados o agendamento que tem este ID exato
    agendamento_alvo = db.query(models.Agendamento).filter(models.Agendamento.id == agendamento_id).first()
    
    # 2. Se ele existir, nós damos a ordem de deletar
    if agendamento_alvo is not None:
        db.delete(agendamento_alvo)
        db.commit() # Confirma a exclusão no disco rígido
        db.close()
        return {"status": "Sucesso", "mensagem": "Agendamento cancelado com sucesso!"}
    
    # 3. Se não encontrar (alguém já deletou antes), avisa o erro
    db.close()
    return {"status": "Erro", "mensagem": "Agendamento não encontrado."}

    #-----------------------------------------#

    # ==========================================
# MÓDULO DE SERVIÇOS (CARDÁPIO DA BARBEARIA)
# ==========================================
# 1. Pydantic para validar a entrada de novos serviços (ATUALIZADO)
class NovoServico(BaseModel):
    nome: str
    preco: float
    duracao: int # NOVO CAMPO AQUI

# 2. Rota para CRIAR um serviço novo (ATUALIZADA)
@app.post("/api/servicos")
def cadastrar_servico(dados: NovoServico):
    db = SessaoLocal()
    novo_servico = models.ServicoBarbearia(
        nome=dados.nome, 
        preco=dados.preco,
        duracao=dados.duracao # SALVANDO O TEMPO AQUI
    )
    db.add(novo_servico)
    db.commit()
    db.close()
    return {"status": "Sucesso", "mensagem": "Serviço cadastrado com sucesso!"}

# 3. Rota para LER todos os serviços salvos
@app.get("/api/servicos")
def listar_servicos():
    db = SessaoLocal()
    todos_servicos = db.query(models.ServicoBarbearia).all()
    db.close()
    return todos_servicos

# 4. Rota para DELETAR um serviço do cardápio
@app.delete("/api/servicos/{servico_id}")
def remover_servico(servico_id: int):
    db = SessaoLocal()
    alvo = db.query(models.ServicoBarbearia).filter(models.ServicoBarbearia.id == servico_id).first()
    
    if alvo is not None:
        db.delete(alvo)
        db.commit()
        db.close()
        return {"status": "Sucesso", "mensagem": "Serviço removido do sistema!"}
    
    db.close()
    return {"status": "Erro", "mensagem": "Serviço não encontrado."}

    #----------------------------------#

# ==========================================
# MÓDULO DE CONFIGURAÇÃO (HORÁRIOS E TEMA)
# ==========================================
class NovaConfiguracao(BaseModel):
    abertura: int
    fechamento: int
    cor_tema: str # O Python agora exige a cor

@app.post("/api/configuracoes")
def salvar_configuracoes(dados: NovaConfiguracao):
    db = SessaoLocal()
    config_atual = db.query(models.ConfiguracaoAgenda).first()
    
    if config_atual is None:
        nova_config = models.ConfiguracaoAgenda(
            hora_abertura=dados.abertura, 
            hora_fechamento=dados.fechamento,
            cor_tema=dados.cor_tema # Salvando a cor
        )
        db.add(nova_config)
    else:
        config_atual.hora_abertura = dados.abertura
        config_atual.hora_fechamento = dados.fechamento
        config_atual.cor_tema = dados.cor_tema # Atualizando a cor
        
    db.commit()
    db.close()
    return {"status": "Sucesso", "mensagem": "Configurações do sistema atualizadas!"}

# ROTA NOVA: O site do cliente vai usar essa rota para descobrir a cor!
@app.get("/api/configuracoes")
def ler_configuracoes():
    db = SessaoLocal()
    config_atual = db.query(models.ConfiguracaoAgenda).first()
    db.close()
    
    # Se o dono nunca configurou nada, mandamos o padrão
    if config_atual is None:
        return {"abertura": 9, "fechamento": 18, "cor_tema": "#f59e0b"}
        
    return {
        "abertura": config_atual.hora_abertura, 
        "fechamento": config_atual.hora_fechamento, 
        "cor_tema": config_atual.cor_tema
    }

    #-------------------------------------------------------#

    # ==========================================
# MÓDULO DE PROFISSIONAIS (EQUIPE)
# ==========================================
class NovoProfissional(BaseModel):
    nome: str

@app.post("/api/profissionais")
def cadastrar_profissional(dados: NovoProfissional):
    db = SessaoLocal()
    novo_prof = models.Profissional(nome=dados.nome)
    db.add(novo_prof)
    db.commit()
    db.close()
    return {"status": "Sucesso", "mensagem": "Profissional adicionado à equipe!"}

@app.get("/api/profissionais")
def listar_profissionais():
    db = SessaoLocal()
    equipe = db.query(models.Profissional).all()
    db.close()
    return equipe

@app.delete("/api/profissionais/{prof_id}")
def remover_profissional(prof_id: int):
    db = SessaoLocal()
    alvo = db.query(models.Profissional).filter(models.Profissional.id == prof_id).first()
    if alvo is not None:
        db.delete(alvo)
        db.commit()
    db.close()
    return {"mensagem": "Profissional removido."}