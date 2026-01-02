import os , json , datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction, models
from django.db.models import Sum
from django.db.models.functions import ExtractMonth, ExtractYear
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from weasyprint import HTML  # Para gerar PDFs
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login

from .models import (
    Residente, Dispositivo, RegistoConsumo, Orcamento_limite,
    Fornecedor, FornecedorTipo, FornecedorValor, FornecedorResidente,
    Tipo, Categoria
)

from .forms import (
    RegistoResidenteForm, DispositivoForm, EditarPerfilForm,
    ConsumoManualForm, CriarMetaForm, EditarMetaForm
)

# Configuração de paths para o GTK
if os.name == 'nt':
    GIO_LIB_PATH = r'C:\Program Files\GTK3-Runtime\bin'
    if os.path.exists(GIO_LIB_PATH):
        os.environ['PATH'] = GIO_LIB_PATH + os.pathsep + os.environ['PATH']

MESES = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio',
    6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro',
    11: 'Novembro', 12: 'Dezembro'
}

# ===== FUNÇÕES HELPERS =====

def _get_residente_or_redirect(user, redirect_to='dashboard'):
    try:
      
        return Residente.objects.get(email=user.email)
    except Residente.DoesNotExist:
   
        if user.is_superuser:
          
            residente_root, created = Residente.objects.get_or_create(
                telemovel='999999999',  
                defaults={
                    'nome': 'Administrador (Root)',
                    'email': user.email,
                    'password': 'root_password_placeholder',
                    'morada': 'Sede Administrativa',
                    'cidade': 'Sistema',
                    'codigo_postal': '0000-000',
                    'status': 1
                }
            )
            if not created and residente_root.email != user.email:
                residente_root.email = user.email
                residente_root.save()
                
            return residente_root
    
        return None

# Função helper para extrair e validar ano e mês dos parâmetros GET
def _parse_ano_mes(request, default_date=None):
    if default_date is None:
        default_date = datetime.date.today()
    try:
        ano = int(request.GET.get('ano', default_date.year))
        mes = int(request.GET.get('mes', default_date.month))
    except ValueError:
        ano, mes = default_date.year, default_date.month
    return ano, mes

#Preços recentes dos fornecedores
def get_latest_price(fornecedor_tipo):
    tarifa = FornecedorValor.objects.filter(fornecedor_tipo=fornecedor_tipo).order_by('-timestamp').first()
    return float(tarifa.valor) if tarifa else 1.0

# Função para obter o contrato ativo de um fornecedor para um tipo (Luz, Água, Gás)
def get_active_contract(residente, tipo_nome):
    return FornecedorResidente.objects.filter(
        residente=residente,
        fornecedor_tipo__tipo__tipo=tipo_nome,
        status=1  # Apenas contratos ativos
    ).order_by('-timestamp').first()

# Função para somar apenas consumo (não produção) de um tipo específico
def somar_apenas_consumo(tipo_nome, registos_base):
    soma = registos_base.filter(
        dispositivo__tipo__tipo=tipo_nome,
        dispositivo__categoria__categoria='Consumidor'
    ).aggregate(Sum('valor'))['valor__sum']
    return float(soma) if soma else 0.0


# Considera consumo líquido de luz (consumo - produção)
def calcular_custos_por_tipo(registos_base, residente):
    # Obter preços dos fornecedores ativos para cada tipo de utilidade
    PRECOS = {}
    for tipo_nome in ('Luz', 'Agua', 'Gas'):
        contrato = get_active_contract(residente, tipo_nome)
        PRECOS[tipo_nome] = get_latest_price(contrato.fornecedor_tipo) if contrato else 1.0

    # Calcular consumo de luz: gasto - produção
    gasto_luz = somar_apenas_consumo('Luz', registos_base)
    producao_luz_val = registos_base.filter(
        dispositivo__tipo__tipo='Luz',
        dispositivo__categoria__categoria='Gerador'
    ).aggregate(Sum('valor'))['valor__sum'] or 0.0

    # Consumo líquido de luz nunca pode ser negativo
    consumo_luz_liquido = max(0, float(gasto_luz) - float(producao_luz_val))
    consumo_agua = somar_apenas_consumo('Agua', registos_base)
    consumo_gas = somar_apenas_consumo('Gas', registos_base)

    # Retorna dicionário com custos calculados (consumo * preço por unidade)
    return {
        'Luz': round(consumo_luz_liquido * PRECOS['Luz'], 2),
        'Agua': round(consumo_agua * PRECOS['Agua'], 2),
        'Gas': round(consumo_gas * PRECOS['Gas'], 2),
    }

def registar(request):
    if request.method == 'POST':
        form = RegistoResidenteForm(request.POST)
        if form.is_valid():
            residente = form.save()
            # Verifica se utilizador Django já existe
            if not User.objects.filter(username=residente.email).exists():
                User.objects.create_user(
                    username=residente.email,
                    email=residente.email,
                    password=residente.password,
                    first_name=residente.nome
                )
            messages.success(request, 'Conta criada! Faça login.')
            return redirect('login')
    else:
        form = RegistoResidenteForm()
    return render(request, 'Gestao_Consumos/registar.html', {'form': form})


@login_required(login_url='login')
def dashboard(request):
    residente = _get_residente_or_redirect(request.user)
    ano, mes = _parse_ano_mes(request)

    registos_mes = RegistoConsumo.objects.filter(
        dispositivo__residente=residente,
        timestamp__year=ano,
        timestamp__month=mes
    )

    custos = calcular_custos_por_tipo(registos_mes, residente)
    gasto_luz_val = registos_mes.filter(
        dispositivo__tipo__tipo='Luz',
        dispositivo__categoria__categoria='Consumidor'
    ).aggregate(Sum('valor'))['valor__sum'] or 0

    prod_luz_val = registos_mes.filter(
        dispositivo__tipo__tipo='Luz',
        dispositivo__categoria__categoria='Gerador'
    ).aggregate(Sum('valor'))['valor__sum'] or 0

    consumo_luz_liquido = max(0, float(gasto_luz_val) - float(prod_luz_val))
    consumo_agua = somar_apenas_consumo('Agua', registos_mes)
    consumo_gas = somar_apenas_consumo('Gas', registos_mes)

    custo_total = round(sum(custos.values()), 2)

    metas_total_query = Orcamento_limite.objects.filter(
        residente=residente, timestamp__month=mes, timestamp__year=ano
    ).aggregate(Sum('valor'))['valor__sum']
    meta_orcamento_total = float(metas_total_query) if metas_total_query else 0.00

    if custo_total > meta_orcamento_total and meta_orcamento_total > 0:
        status_alerta = 'excedido'
    elif meta_orcamento_total > 0:
        status_alerta = 'dentro'
    else:
        status_alerta = 'sem_meta'

    dispositivos = Dispositivo.objects.filter(residente=residente)

    # Prepara contexto para template
    context = {
        'residente': residente,
        'dispositivos': dispositivos,
        'total_dispositivos': dispositivos.count(),
        'ano_atual': ano,
        'mes_atual': mes,
        'anos_range': range(2025, 2031),
        'meses_range': range(1, 13),
        'consumo_luz': round(consumo_luz_liquido, 2),
        'consumo_agua': round(consumo_agua, 2),
        'consumo_gas': round(consumo_gas, 2),
        'custo_luz': custos['Luz'],
        'custo_agua': custos['Agua'],
        'custo_gas': custos['Gas'],
        'custo_total': custo_total,
        'meta_orcamento_total': round(meta_orcamento_total, 2),
        'status_alerta': status_alerta,
    }
    return render(request, 'Gestao_Consumos/dashboard.html', context)



@login_required(login_url='login')
def adicionar_dispositivo(request):
    residente = _get_residente_or_redirect(request.user)
    if request.method == 'POST':
        form = DispositivoForm(request.POST)
        if form.is_valid():
            try:
                # Cria dispositivo associado ao residente
                dispositivo = form.save(commit=False)
                dispositivo.residente = residente
                dispositivo.save()
                messages.success(request, 'Dispositivo adicionado com sucesso!')
                return redirect('lista_dispositivos')
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = DispositivoForm()

    dispositivos = Dispositivo.objects.filter(residente=residente)
    context = {
        'form': form,
        'residente': residente,
        'dispositivos': dispositivos,
        'modal_error': True if form.non_field_errors else False
    }
    return render(request, 'Gestao_Consumos/lista_dispositivos.html', context)


@login_required(login_url='login')
def editar_dispositivo_post(request, id):
    dispositivo = get_object_or_404(Dispositivo, pk=id)
    if request.method == 'POST':
        form = DispositivoForm(request.POST, instance=dispositivo)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'Dispositivo "{dispositivo.nome}" atualizado!')
            except ValidationError as e:
                messages.error(request, f'Erro ao atualizar: {e.message}')
    return redirect('lista_dispositivos')


@login_required(login_url='login')
def lista_dispositivos(request):
    residente = _get_residente_or_redirect(request.user)
    if not residente:
        return redirect('dashboard')

    dispositivos = Dispositivo.objects.filter(residente=residente)
    form = DispositivoForm()
    return render(request, 'Gestao_Consumos/lista_dispositivos.html', {
        'dispositivos': dispositivos,
        'residente': residente,
        'form': form,
        'modal_error': False
    })

@login_required(login_url='login')
def apagar_dispositivo(request, id):
    residente = _get_residente_or_redirect(request.user)
    dispositivo = get_object_or_404(Dispositivo, pk=id, residente=residente)
    try:
        with transaction.atomic():
            RegistoConsumo.objects.filter(dispositivo=dispositivo).delete()
            dispositivo.delete()
    except Exception as e:
        messages.error(request, f'Erro ao apagar dispositivo: {e}')

    return redirect('lista_dispositivos')

@login_required(login_url='login')
def registar_consumo(request):
    residente = _get_residente_or_redirect(request.user)
    if request.method == 'POST':
        form = ConsumoManualForm(residente, request.POST)
        if form.is_valid():
            registo = form.save(commit=False)
            mes = int(form.cleaned_data['mes'])
            ano = int(form.cleaned_data['ano'])
            registo.timestamp = datetime.datetime(ano, mes, 1, 12, 0, 0)
            registo.save()
            messages.success(request, 'Consumo registado com sucesso!')
            return redirect('registar_consumo')
    else:
        form = ConsumoManualForm(residente)

    # Obtém histórico de registos (mais recentes primeiro)
    historico = RegistoConsumo.objects.filter(dispositivo__residente=residente).order_by('-timestamp')
    return render(request, 'Gestao_Consumos/registar_consumo.html', {
        'form': form,
        'historico': historico,
        'residente': residente
    })

@login_required(login_url='login')
def editar_consumo(request, id):
    registo = get_object_or_404(RegistoConsumo, pk=id)
    residente = _get_residente_or_redirect(request.user)
    if request.method == 'POST':
        form = ConsumoManualForm(residente, request.POST, instance=registo)
        if form.is_valid():
            registo_editado = form.save(commit=False)
            mes = int(form.cleaned_data['mes'])
            ano = int(form.cleaned_data['ano'])
            registo_editado.timestamp = datetime.datetime(ano, mes, 1, 12, 0, 0)
            registo_editado.save()
            messages.success(request, 'Atualizado com sucesso!')
            return redirect('registar_consumo')
    else:
        dados_iniciais = {'mes': registo.timestamp.month, 'ano': registo.timestamp.year}
        form = ConsumoManualForm(residente, instance=registo, initial=dados_iniciais)

    return render(request, 'Gestao_Consumos/editar_consumo.html', {'form': form, 'registo': registo})


@login_required(login_url='login')
def apagar_consumo(request, id):
    registo = get_object_or_404(RegistoConsumo, pk=id)
    if registo.dispositivo.residente.email == request.user.email:
        registo.delete()
        messages.success(request, 'Registo eliminado.')
    return redirect('registar_consumo')



@login_required(login_url='login')
def definicoes(request):
    residente = _get_residente_or_redirect(request.user)
    if not residente:
        return redirect('dashboard')

    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, instance=residente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado!')
            return redirect('definicoes')
    else:
        form = EditarPerfilForm(instance=residente)

    return render(request, 'Gestao_Consumos/definicoes.html', {'form': form, 'residente': residente})



@login_required(login_url='login')
def relatorios(request):
    residente = _get_residente_or_redirect(request.user)
    if not residente:
        return redirect('dashboard')

    hoje = datetime.date.today()
    ano_selecionado, mes_selecionado = _parse_ano_mes(request, hoje)
    nome_mes_atual = MESES.get(mes_selecionado, None)

    if request.method == 'POST':
        form = CriarMetaForm(request.POST)
        if form.is_valid():
            exists = Orcamento_limite.objects.filter(
                residente=residente,
                tipo=form.cleaned_data['tipo'],
                timestamp__month=form.cleaned_data['mes'],
                timestamp__year=form.cleaned_data['ano']
            ).exists()
            if exists:
                return redirect(f"/relatorios/?ano={ano_selecionado}&mes={mes_selecionado}")
            try:
                form.save(residente_obj=residente, commit=True)
            except Exception as e:
                messages.error(request, f'Erro interno ao salvar a meta: {e}')
                return redirect(f"/relatorios/?ano={ano_selecionado}&mes={mes_selecionado}")
            messages.success(request, 'Meta de orçamento adicionada com sucesso!')
            return redirect(f"/relatorios/?ano={ano_selecionado}&mes={mes_selecionado}")
    else:
        form = CriarMetaForm()

    registos_base = RegistoConsumo.objects.filter(dispositivo__residente=residente)
    registos_mes = registos_base.filter(timestamp__year=ano_selecionado, timestamp__month=mes_selecionado)

    custos_mensais = calcular_custos_por_tipo(registos_mes, residente)
    # Prepara dados do gráfico de distribuição
    dados_distribuicao = {'labels': list(custos_mensais.keys()), 'data': list(custos_mensais.values())}

    registos_ano = registos_base.filter(timestamp__year=ano_selecionado)
    trend_data = {}
    for mes_num in range(1, 13):
        custos_mes_loop = calcular_custos_por_tipo(
            registos_ano.filter(timestamp__month=mes_num), residente
        )
        trend_data[mes_num] = round(sum(custos_mes_loop.values()), 2)

    MESES_NOMES_LIST = [MESES[i] for i in range(1, 13)]
    # Prepara dados do gráfico de tendência 
    dados_tendencia = {'labels': MESES_NOMES_LIST, 'data': [trend_data.get(m + 1, 0) for m in range(12)]}

    historico_metas = Orcamento_limite.objects.filter(residente=residente).order_by('-timestamp')

    return render(request, 'Gestao_Consumos/relatorios.html', {
        'residente': residente,
        'form': form,
        'metas': historico_metas,
        'ano_atual': ano_selecionado,
        'mes_atual': mes_selecionado,
        'nome_mes_atual': nome_mes_atual,
        
        'anos_range': range(2025, 2031),
        'meses_nomes': [(i + 1, MESES_NOMES_LIST[i]) for i in range(12)],
        'dados_distribuicao_json': json.dumps(dados_distribuicao),
        'dados_tendencia_json': json.dumps(dados_tendencia),
    })

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@login_required(login_url='login')
def editar_meta(request, id):
    residente = _get_residente_or_redirect(request.user)
    meta = get_object_or_404(Orcamento_limite, pk=id, residente=residente)
    if request.method == 'POST':
        form = EditarMetaForm(request.POST, instance=meta)
        if form.is_valid():
            form.save()
            return redirect('relatorios')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = EditarMetaForm(instance=meta)
    context = {
        'form': form,
        'meta': meta,
    }
    return render(request, 'Gestao_Consumos/editar_meta.html', context)

@login_required(login_url='login')
def apagar_meta(request, id):
    residente = _get_residente_or_redirect(request.user)
    meta = get_object_or_404(Orcamento_limite, pk=id, residente=residente)
    meta.delete()
    return redirect('relatorios')


@login_required(login_url='login')
def gerar_pdf(request, tipo, ano, mes):
    residente = _get_residente_or_redirect(request.user)
    if not residente:
        return redirect('dashboard')

    registos_base_geral = RegistoConsumo.objects.filter(dispositivo__residente=residente, timestamp__year=ano)

    metas_ano_dict = {
        (m.timestamp.month, m.tipo.tipo): float(m.valor)
        for m in Orcamento_limite.objects.filter(residente=residente, timestamp__year=ano)
    }

    if tipo == 'mensal':
        registos_mensais = registos_base_geral.filter(timestamp__month=mes)
        custos_calculados = calcular_custos_por_tipo(registos_mensais, residente)
        alerta_status = {}
        for utilidade, custo_real in custos_calculados.items():
            meta = metas_ano_dict.get((mes, utilidade), 0.00)
            custo_real_float = float(custo_real)
            excedido = custo_real_float > meta and meta > 0
            alerta_status[utilidade] = {
                'custo': custo_real_float,
                'meta': meta,
                'status': 'excedido' if excedido else 'ok',
                'mensagem': f"EXCEDEU em {round(custo_real_float - meta, 2)} €" if excedido else "Dentro do limite.",
            }

        contexto_pdf = {
            'residente': residente,
            'periodo': f"Relatório Mensal ({mes}/{ano})",
            'alerta_status': alerta_status,
            'custo_total': sum(c['custo'] for c in alerta_status.values()),
            'data_hoje': datetime.date.today().strftime('%d/%m/%Y'),
            'tipo_relatorio': tipo,
            'ano': ano,
        }

    elif tipo == 'anual':
        relatorio_anual_detalhado = []
        custo_anual_total = 0.0
        for m in range(1, 13):
            registos_mensais = registos_base_geral.filter(timestamp__month=m)
            custos_mensais = calcular_custos_por_tipo(registos_mensais, residente)

            detalhe_mensal = {'mes_nome': MESES.get(m, 'Mês Desconhecido'), 'custo_total_mes': 0.0, 'utilidades': []}
            tem_dados_no_mes = False
            for utilidade in ('Luz', 'Agua', 'Gas'):
                custo_real_float = float(custos_mensais.get(utilidade, 0.00))
                meta = metas_ano_dict.get((m, utilidade), 0.00)
                if custo_real_float > 0.00 or meta > 0.00:
                    tem_dados_no_mes = True
                excedido = custo_real_float > meta and meta > 0
                detalhe_mensal['utilidades'].append({
                    'utilidade': utilidade,
                    'meta': meta,
                    'custo': custo_real_float,
                    'status': 'excedido' if excedido else 'ok',
                    'mensagem': f"EXCEDEU em {round(custo_real_float - meta, 2)} €" if excedido else "Dentro do limite.",
                })
                detalhe_mensal['custo_total_mes'] += custo_real_float
                custo_anual_total += custo_real_float
            if tem_dados_no_mes:
                relatorio_anual_detalhado.append(detalhe_mensal)

        contexto_pdf = {
            'residente': residente,
            'periodo': f"Relatório Anual ({ano})",
            'relatorio_anual_detalhado': relatorio_anual_detalhado,
            'custo_total': custo_anual_total,
            'data_hoje': datetime.date.today().strftime('%d/%m/%Y'),
            'tipo_relatorio': tipo,
            'ano': ano,
        }
    else:
        return HttpResponse("Tipo de relatório inválido.", status=400)

    html_string = render_to_string('Gestao_Consumos/relatorio_base.html', contexto_pdf)
    html = HTML(string=html_string)
    pdf = html.write_pdf()

    nome_ficheiro = f"Relatorio_{tipo}_{ano}"
    if tipo == 'mensal':
        nome_ficheiro += f"_{mes}"

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nome_ficheiro}.pdf"'
    return response


@login_required(login_url='login')
def lista_fornecedores(request):
    residente = _get_residente_or_redirect(request.user)
    fornecedores_data = []
    for fornecedor in Fornecedor.objects.filter(status=1):
        servicos_data = []
        servicos_oferecidos = FornecedorTipo.objects.filter(fornecedor=fornecedor, status=1)
        for servico in servicos_oferecidos:
            servicos_data.append({
                'servico_tipo': servico.tipo.tipo,
                'tarifa_valor': get_latest_price(servico),
                'unidade': servico.unidade,
                'fornecedor_tipo_pk': servico.pk,
            })
        if servicos_data:
            fornecedores_data.append({'info': {'id': fornecedor.pk, 'nome': fornecedor.nome}, 'servicos': servicos_data})

    contrato_luz = get_active_contract(residente, 'Luz')
    contrato_agua = get_active_contract(residente, 'Agua')
    contrato_gas = get_active_contract(residente, 'Gas')

    residente_fornecedores = {
        'Luz': contrato_luz.fornecedor_tipo.fornecedor.pk if contrato_luz else None,
        'Agua': contrato_agua.fornecedor_tipo.fornecedor.pk if contrato_agua else None,
        'Gas': contrato_gas.fornecedor_tipo.fornecedor.pk if contrato_gas else None,
    }

    return render(request, 'Gestao_Consumos/fornecedores.html', {
        'fornecedores_data': fornecedores_data,
        'residente_fornecedores': residente_fornecedores,
        'residente': residente,
    })


@login_required(login_url='login')
def associar_fornecedor(request):
    if request.method != 'POST':
        return redirect('lista_fornecedores')

    fornecedor_tipo_pk = request.POST.get('fornecedor_tipo_pk')
    residente = _get_residente_or_redirect(request.user)
    fornecedor_tipo_obj = FornecedorTipo.objects.get(pk=fornecedor_tipo_pk)
    servico_tipo = fornecedor_tipo_obj.tipo.tipo
    with transaction.atomic():
        FornecedorResidente.objects.filter(
            residente=residente,
            fornecedor_tipo__tipo__tipo=servico_tipo,
            status=1
        ).update(status=0)

        FornecedorResidente.objects.create(
            residente=residente,
            fornecedor_tipo=fornecedor_tipo_obj,
            status=1,
            timestamp=datetime.datetime.now()
        )
    messages.success(
        request,
        f"O seu fornecedor de {servico_tipo} foi atualizado para {fornecedor_tipo_obj.fornecedor.nome}."
    )
    return redirect('lista_fornecedores')

def is_superuser_check(user):
    return user.is_superuser


@user_passes_test(is_superuser_check)
def gerir_utilizadores(request):
   
    emails_root = User.objects.filter(is_superuser=True).values_list('email', flat=True)


    residentes = Residente.objects.exclude(email__in=emails_root).order_by('nome')
    

    for r in residentes:
        contratos = FornecedorResidente.objects.filter(residente=r, status=1)
        lista_fornecedores = []
        for c in contratos:
            nome = c.fornecedor_tipo.fornecedor.nome
            tipo = c.fornecedor_tipo.tipo.tipo
            lista_fornecedores.append(f"{nome} ({tipo})")
        
        r.lista_empresas = lista_fornecedores

    return render(request, 'Gestao_Consumos/gerir_utilizadores.html', {
        'residentes': residentes
    })
@user_passes_test(is_superuser_check)
def alterar_estado_residente(request, id_residente):
    residente = get_object_or_404(Residente, pk=id_residente)
    
    
    novo_status = 0 if residente.status == 1 else 1
    residente.status = novo_status
    residente.save()
    
    try:
        user_django = User.objects.get(email=residente.email)
        user_django.is_active = True if novo_status == 1 else False
        user_django.save()
        msg_tipo = "Ativado" if novo_status == 1 else "Bloqueado"
        messages.success(request, f'Utilizador {residente.nome} foi {msg_tipo} com sucesso.')
    except User.DoesNotExist:
        messages.warning(request, 'Estado alterado no Residente, mas conta de Login não encontrada.')

    return redirect('gerir_utilizadores')


def login_user(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username_input = request.POST.get('username')
        password_input = request.POST.get('password')

        user = authenticate(request, username=username_input, password=password_input)

        if user is not None:

            login(request, user)
            return redirect('dashboard')
        else:
    
            try:
            
                utilizador_verificao = User.objects.get(username=username_input)
                
                if not utilizador_verificao.is_active:
                   
                    messages.error(request, 'Está bloqueado pelo sistema administrativo')
                else:
                
                    messages.error(request, 'Dados incorretos. Verifique o email e a password.')
            
            except User.DoesNotExist:
                messages.error(request, 'Dados incorretos. Verifique o email e a password.')

    return render(request, 'Gestao_Consumos/login.html')