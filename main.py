from fastapi import FastAPI
from pydantic import BaseModel
from database import engine, Base, SessaoLocal
import models
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware

# Inicia a API (UMA ÚNICA VEZ)
app = FastAPI()

# O "CARIMBO DE AUTORIZAÇÃO" DO CORS (Liberando as fronteiras)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

# ==========================================
# MÓDULO DE AGENDAMENTOS
# ==========================================
class FichaAgendamento(BaseModel):
    cliente_nome: str
    servico: str
    horario: str
    valor: float
    profissional: str 

@app.post("/api/agendar")
def criar_agendamento(dados_recebidos: FichaAgendamento):
    db = SessaoLocal()
    novo_agendamento = models.Agendamento(
        cliente_nome=dados_recebidos.cliente_nome,
        servico=dados_recebidos.servico,
        horario=dados_recebidos.horario,
        valor=dados_recebidos.valor,
        profissional=dados_recebidos.profissional 
    )
    db.add(novo_agendamento)
    db.commit()
    db.close()
    return {"status": "Sucesso", "mensagem": f"Agendamento confirmado com {dados_recebidos.profissional}!"}

@app.get("/api/agendamentos")
def listar_todos_agendamentos():
    db = SessaoLocal()
    todos_os_agendamentos = db.query(models.Agendamento).all()
    db.close()
    return todos_os_agendamentos

@app.delete("/api/agendamentos/{agendamento_id}")
def cancelar_agendamento(agendamento_id: int):
    db = SessaoLocal()
    agendamento_alvo = db.query(models.Agendamento).filter(models.Agendamento.id == agendamento_id).first()
    if agendamento_alvo is not None:
        db.delete(agendamento_alvo)
        db.commit() 
        db.close()
        return {"status": "Sucesso", "mensagem": "Agendamento cancelado com sucesso!"}
    db.close()
    return {"status": "Erro", "mensagem": "Agendamento não encontrado."}

@app.get("/api/horarios/{duracao_minutos}/{profissional}")
def obter_horarios_fatiados(duracao_minutos: int, profissional: str):
    db = SessaoLocal()
    
    config = db.query(models.ConfiguracaoAgenda).first()
    abertura = 9  
    fechamento = 18
    if config is not None:
        abertura = config.hora_abertura
        fechamento = config.hora_fechamento

    agendamentos_do_barbeiro = db.query(models.Agendamento).filter(models.Agendamento.profissional == profissional).all()
    
    intervalos_ocupados = []
    for agendamento in agendamentos_do_barbeiro:
        servico_cadastrado = db.query(models.ServicoBarbearia).filter(models.ServicoBarbearia.nome == agendamento.servico).first()
        duracao_ocupada = 30 
        if servico_cadastrado is not None:
            duracao_ocupada = servico_cadastrado.duracao
            
        inicio_existente = datetime.strptime(agendamento.horario, "%H:%M")
        fim_existente = inicio_existente + timedelta(minutes=duracao_ocupada)
        intervalos_ocupados.append((inicio_existente, fim_existente))
        
    db.close()

    hora_atual = datetime.strptime(f"{abertura}:00", "%H:%M")
    hora_fim = datetime.strptime(f"{fechamento}:00", "%H:%M")
    passo_grade = timedelta(minutes=duracao_minutos)

    horarios_livres = []
    
    while (hora_atual + timedelta(minutes=duracao_minutos)) <= hora_fim:
        inicio_proposto = hora_atual
        fim_proposto = hora_atual + timedelta(minutes=duracao_minutos)
        
        colisao = False
        for inicio_existente, fim_existente in intervalos_ocupados:
            if max(inicio_proposto, inicio_existente) < min(fim_proposto, fim_existente):
                colisao = True
                break
        
        if not colisao:
            horarios_livres.append(hora_atual.strftime("%H:%M"))
            
        hora_atual += passo_grade

    return {"horarios_disponiveis": horarios_livres}

# ==========================================
# MÓDULO DE SERVIÇOS (CARDÁPIO DA BARBEARIA)
# ==========================================
class NovoServico(BaseModel):
    nome: str
    preco: float
    duracao: int 

@app.post("/api/servicos")
def cadastrar_servico(dados: NovoServico):
    db = SessaoLocal()
    novo_servico = models.ServicoBarbearia(
        nome=dados.nome, 
        preco=dados.preco,
        duracao=dados.duracao 
    )
    db.add(novo_servico)
    db.commit()
    db.close()
    return {"status": "Sucesso", "mensagem": "Serviço cadastrado com sucesso!"}

@app.get("/api/servicos")
def listar_servicos():
    db = SessaoLocal()
    todos_servicos = db.query(models.ServicoBarbearia).all()
    db.close()
    return todos_servicos

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

# ==========================================
# MÓDULO DE CONFIGURAÇÃO (HORÁRIOS E TEMA)
# ==========================================
class NovaConfiguracao(BaseModel):
    abertura: int
    fechamento: int
    cor_tema: str 

@app.post("/api/configuracoes")
def salvar_configuracoes(dados: NovaConfiguracao):
    db = SessaoLocal()
    config_atual = db.query(models.ConfiguracaoAgenda).first()
    
    if config_atual is None:
        nova_config = models.ConfiguracaoAgenda(
            hora_abertura=dados.abertura, 
            hora_fechamento=dados.fechamento,
            cor_tema=dados.cor_tema 
        )
        db.add(nova_config)
    else:
        config_atual.hora_abertura = dados.abertura
        config_atual.hora_fechamento = dados.fechamento
        config_atual.cor_tema = dados.cor_tema 
        
    db.commit()
    db.close()
    return {"status": "Sucesso", "mensagem": "Configurações do sistema atualizadas!"}

@app.get("/api/configuracoes")
def ler_configuracoes():
    db = SessaoLocal()
    config_atual = db.query(models.ConfiguracaoAgenda).first()
    db.close()
    if config_atual is None:
        return {"abertura": 9, "fechamento": 18, "cor_tema": "#f59e0b"}
        
    return {
        "abertura": config_atual.hora_abertura, 
        "fechamento": config_atual.hora_fechamento, 
        "cor_tema": config_atual.cor_tema
    }

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