import calendar
import csv
import io
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import (
    Blueprint,
    Response,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import extract

from extensions import db
from models import Cartao, Categoria, Conta, Meta, Transacao

financeiro = Blueprint("financeiro", __name__)


def calcular_saldo_conta(conta):
    transacoes_conta = Transacao.query.filter_by(conta_id=conta.id).all()
    total_receitas = sum(
        (t.valor for t in transacoes_conta if t.tipo == "receita"),
        Decimal("0.00")
    )
    total_despesas = sum(
        (t.valor for t in transacoes_conta if t.tipo == "despesa"),
        Decimal("0.00")
    )
    return conta.saldo_inicial + total_receitas - total_despesas


def adicionar_meses(data_base, meses):
    mes_total = data_base.month - 1 + meses
    ano = data_base.year + mes_total // 12
    mes = mes_total % 12 + 1
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    dia = min(data_base.day, ultimo_dia)
    return date(ano, mes, dia)


@financeiro.route("/")
@login_required
def dashboard():
    hoje = date.today()
    mes = request.args.get("mes", default=hoje.month, type=int)
    ano = request.args.get("ano", default=hoje.year, type=int)

    contas = Conta.query.filter_by(usuario_id=current_user.id).all()
    contas_com_saldo = [
        {"conta": conta, "saldo_atual": calcular_saldo_conta(conta)}
        for conta in contas
    ]
    saldo_total = sum((item["saldo_atual"] for item in contas_com_saldo), Decimal("0.00"))

    transacoes_mes = (
        Transacao.query
        .filter(
            Transacao.usuario_id == current_user.id,
            extract("month", Transacao.data) == mes,
            extract("year", Transacao.data) == ano
        )
        .order_by(Transacao.data.desc(), Transacao.id.desc())
        .all()
    )

    total_receitas = sum((t.valor for t in transacoes_mes if t.tipo == "receita"), Decimal("0.00"))
    total_despesas = sum((t.valor for t in transacoes_mes if t.tipo == "despesa"), Decimal("0.00"))

    # Agrupamento de despesas por categoria no mês
    gastos_por_categoria = {}
    for t in transacoes_mes:
        if t.tipo == "despesa":
            nome_cat = t.categoria.nome
            gastos_por_categoria[nome_cat] = gastos_por_categoria.get(nome_cat, Decimal("0.00")) + t.valor

    resumo_categorias = []
    for nome_cat, total_cat in sorted(gastos_por_categoria.items(), key=lambda x: x[1], reverse=True):
        percentual = (total_cat / total_despesas * 100) if total_despesas > 0 else Decimal("0.00")
        resumo_categorias.append({
            "categoria": nome_cat,
            "total": total_cat,
            "percentual": percentual
        })

    return render_template(
        "dashboard.html",
        contas_com_saldo=contas_com_saldo,
        saldo_total=saldo_total,
        total_receitas=total_receitas,
        total_despesas=total_despesas,
        ultimas_transacoes=transacoes_mes[:5],
        resumo_categorias=resumo_categorias,
        mes_atual=mes,
        ano_atual=ano
    )


@financeiro.route("/contas", methods=["GET", "POST"])
@login_required
def contas():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        tipo = request.form.get("tipo", "").strip()
        saldo_texto = request.form.get("saldo_inicial", "0").strip().replace(",", ".")

        if not nome or tipo == "":
            flash("Preencha o nome e o tipo da conta.")
            return redirect(url_for("financeiro.contas"))

        try:
            saldo_inicial = Decimal(saldo_texto)
        except InvalidOperation:
            flash("Valor de saldo inicial inválido.")
            return redirect(url_for("financeiro.contas"))

        nova_conta = Conta(
            nome=nome,
            tipo=tipo,
            saldo_inicial=saldo_inicial,
            usuario_id=current_user.id
        )

        db.session.add(nova_conta)
        db.session.commit()

        flash("Conta cadastrada com sucesso!")
        return redirect(url_for("financeiro.contas"))

    lista_contas = Conta.query.filter_by(usuario_id=current_user.id).all()
    return render_template("contas.html", contas=lista_contas)


@financeiro.route("/contas/<int:conta_id>/excluir", methods=["POST"])
@login_required
def excluir_conta(conta_id):
    conta = Conta.query.filter_by(id=conta_id, usuario_id=current_user.id).first_or_404()
    if conta.transacoes:
        flash("Não é possível excluir uma conta que já possui transações vinculadas.")
        return redirect(url_for("financeiro.contas"))

    db.session.delete(conta)
    db.session.commit()
    flash("Conta excluída com sucesso!")
    return redirect(url_for("financeiro.contas"))


@financeiro.route("/categorias", methods=["GET", "POST"])
@login_required
def categorias():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        tipo = request.form.get("tipo", "").strip()

        if not nome or tipo not in ("receita", "despesa"):
            flash("Informe um nome válido e selecione receita ou despesa.")
            return redirect(url_for("financeiro.categorias"))

        nova_categoria = Categoria(
            nome=nome,
            tipo=tipo,
            usuario_id=current_user.id
        )

        db.session.add(nova_categoria)
        db.session.commit()

        flash("Categoria cadastrada com sucesso!")
        return redirect(url_for("financeiro.categorias"))

    lista_categorias = Categoria.query.filter_by(usuario_id=current_user.id).all()
    return render_template("categorias.html", categorias=lista_categorias)


@financeiro.route("/categorias/<int:categoria_id>/excluir", methods=["POST"])
@login_required
def excluir_categoria(categoria_id):
    categoria = Categoria.query.filter_by(id=categoria_id, usuario_id=current_user.id).first_or_404()
    if categoria.transacoes:
        flash("Não é possível excluir uma categoria que já possui transações vinculadas.")
        return redirect(url_for("financeiro.categorias"))

    db.session.delete(categoria)
    db.session.commit()
    flash("Categoria excluída com sucesso!")
    return redirect(url_for("financeiro.categorias"))


@financeiro.route("/transacoes", methods=["GET", "POST"])
@login_required
def transacoes():
    contas_usuario = Conta.query.filter_by(usuario_id=current_user.id).all()
    categorias_usuario = Categoria.query.filter_by(usuario_id=current_user.id).all()

    if request.method == "POST":
        descricao = request.form.get("descricao", "").strip()
        valor_texto = request.form.get("valor", "").strip().replace(",", ".")
        tipo = request.form.get("tipo", "").strip()
        data_texto = request.form.get("data", "").strip()
        conta_id = request.form.get("conta_id", type=int)
        categoria_id = request.form.get("categoria_id", type=int)
        repetir_meses = request.form.get("repetir_meses", default=1, type=int)

        if not descricao or not valor_texto or tipo not in ("receita", "despesa") or not data_texto:
            flash("Preencha todos os campos da transação.")
            return redirect(url_for("financeiro.transacoes"))

        try:
            valor = Decimal(valor_texto)
            if valor <= 0:
                raise InvalidOperation
        except InvalidOperation:
            flash("Informe um valor numérico maior que zero.")
            return redirect(url_for("financeiro.transacoes"))

        try:
            data_base = datetime.strptime(data_texto, "%Y-%m-%d").date()
        except ValueError:
            flash("Data inválida.")
            return redirect(url_for("financeiro.transacoes"))

        conta = Conta.query.filter_by(id=conta_id, usuario_id=current_user.id).first()
        categoria = Categoria.query.filter_by(id=categoria_id, usuario_id=current_user.id).first()

        if not conta or not categoria:
            flash("Selecione uma conta e uma categoria válidas.")
            return redirect(url_for("financeiro.transacoes"))

        repeticoes = max(1, min(repetir_meses or 1, 60))

        for i in range(repeticoes):
            desc_final = f"{descricao} ({i + 1}/{repeticoes})" if repeticoes > 1 else descricao
            data_parcela = adicionar_meses(data_base, i)

            nova_transacao = Transacao(
                descricao=desc_final,
                valor=valor,
                tipo=tipo,
                data=data_parcela,
                usuario_id=current_user.id,
                conta_id=conta.id,
                categoria_id=categoria.id
            )
            db.session.add(nova_transacao)

        db.session.commit()

        if repeticoes > 1:
            flash(f"{repeticoes} lançamentos mensais registrados com sucesso!")
        else:
            flash("Transação registrada com sucesso!")
        return redirect(url_for("financeiro.transacoes"))

    # Filtros via GET
    hoje = date.today()
    mes = request.args.get("mes", default=hoje.month, type=int)
    ano = request.args.get("ano", default=hoje.year, type=int)
    filtro_tipo = request.args.get("tipo", "").strip()
    filtro_conta = request.args.get("conta_id", type=int)
    filtro_categoria = request.args.get("categoria_id", type=int)

    query = Transacao.query.filter(
        Transacao.usuario_id == current_user.id,
        extract("month", Transacao.data) == mes,
        extract("year", Transacao.data) == ano
    )

    if filtro_tipo in ("receita", "despesa"):
        query = query.filter(Transacao.tipo == filtro_tipo)
    if filtro_conta:
        query = query.filter(Transacao.conta_id == filtro_conta)
    if filtro_categoria:
        query = query.filter(Transacao.categoria_id == filtro_categoria)

    lista_transacoes = query.order_by(Transacao.data.desc(), Transacao.id.desc()).all()

    return render_template(
        "transacoes.html",
        transacoes=lista_transacoes,
        contas=contas_usuario,
        categorias=categorias_usuario,
        mes_atual=mes,
        ano_atual=ano,
        filtro_tipo=filtro_tipo,
        filtro_conta=filtro_conta,
        filtro_categoria=filtro_categoria
    )


@financeiro.route("/transacoes/exportar")
@login_required
def exportar_transacoes():
    hoje = date.today()
    mes = request.args.get("mes", default=hoje.month, type=int)
    ano = request.args.get("ano", default=hoje.year, type=int)
    filtro_tipo = request.args.get("tipo", "").strip()
    filtro_conta = request.args.get("conta_id", type=int)
    filtro_categoria = request.args.get("categoria_id", type=int)

    query = Transacao.query.filter(
        Transacao.usuario_id == current_user.id,
        extract("month", Transacao.data) == mes,
        extract("year", Transacao.data) == ano
    )

    if filtro_tipo in ("receita", "despesa"):
        query = query.filter(Transacao.tipo == filtro_tipo)
    if filtro_conta:
        query = query.filter(Transacao.conta_id == filtro_conta)
    if filtro_categoria:
        query = query.filter(Transacao.categoria_id == filtro_categoria)

    lista_transacoes = query.order_by(Transacao.data.asc(), Transacao.id.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Data", "Descrição", "Categoria", "Conta", "Tipo", "Valor (R$)"])

    for t in lista_transacoes:
        writer.writerow([
            f" {t.data.strftime('%d/%m/%Y')}",
            t.descricao,
            t.categoria.nome,
            t.conta.nome,
            t.tipo.capitalize(),
            f"{t.valor:.2f}".replace(".", ",")
        ])

    conteudo_csv = "\ufeff" + output.getvalue()
    nome_arquivo = f"financeflow_{mes:02d}_{ano}.csv"

    return Response(
        conteudo_csv,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={nome_arquivo}"}
    )


@financeiro.route("/transacoes/<int:transacao_id>/editar", methods=["GET", "POST"])
@login_required
def editar_transacao(transacao_id):
    transacao = Transacao.query.filter_by(id=transacao_id, usuario_id=current_user.id).first_or_404()
    contas_usuario = Conta.query.filter_by(usuario_id=current_user.id).all()
    categorias_usuario = Categoria.query.filter_by(usuario_id=current_user.id).all()

    if request.method == "POST":
        descricao = request.form.get("descricao", "").strip()
        valor_texto = request.form.get("valor", "").strip().replace(",", ".")
        tipo = request.form.get("tipo", "").strip()
        data_texto = request.form.get("data", "").strip()
        conta_id = request.form.get("conta_id", type=int)
        categoria_id = request.form.get("categoria_id", type=int)

        if not descricao or not valor_texto or tipo not in ("receita", "despesa") or not data_texto:
            flash("Preencha todos os campos.")
            return redirect(url_for("financeiro.editar_transacao", transacao_id=transacao.id))

        try:
            valor = Decimal(valor_texto)
            if valor <= 0:
                raise InvalidOperation
            data_transacao = datetime.strptime(data_texto, "%Y-%m-%d").date()
        except (InvalidOperation, ValueError):
            flash("Valor ou data inválidos.")
            return redirect(url_for("financeiro.editar_transacao", transacao_id=transacao.id))

        conta = Conta.query.filter_by(id=conta_id, usuario_id=current_user.id).first()
        categoria = Categoria.query.filter_by(id=categoria_id, usuario_id=current_user.id).first()

        if not conta or not categoria:
            flash("Conta ou categoria inválida.")
            return redirect(url_for("financeiro.editar_transacao", transacao_id=transacao.id))

        transacao.descricao = descricao
        transacao.valor = valor
        transacao.tipo = tipo
        transacao.data = data_transacao
        transacao.conta_id = conta.id
        transacao.categoria_id = categoria.id

        db.session.commit()
        flash("Transação atualizada com sucesso!")
        return redirect(url_for("financeiro.transacoes"))

    return render_template(
        "editar_transacao.html",
        transacao=transacao,
        contas=contas_usuario,
        categorias=categorias_usuario
    )


@financeiro.route("/transacoes/<int:transacao_id>/excluir", methods=["POST"])
@login_required
def excluir_transacao(transacao_id):
    transacao = Transacao.query.filter_by(id=transacao_id, usuario_id=current_user.id).first_or_404()
    db.session.delete(transacao)
    db.session.commit()
    flash("Transação excluída com sucesso!")
    return redirect(url_for("financeiro.transacoes"))


@financeiro.route("/cartoes", methods=["GET", "POST"])
@login_required
def cartoes():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        limite_texto = request.form.get("limite", "").strip().replace(",", ".")
        dia_fechamento = request.form.get("dia_fechamento", type=int)
        dia_vencimento = request.form.get("dia_vencimento", type=int)

        if not nome or not limite_texto or not dia_fechamento or not dia_vencimento:
            flash("Preencha todos os campos do cartão.")
            return redirect(url_for("financeiro.cartoes"))

        if not (1 <= dia_fechamento <= 31) or not (1 <= dia_vencimento <= 31):
            flash("Os dias de fechamento e vencimento devem estar entre 1 e 31.")
            return redirect(url_for("financeiro.cartoes"))

        try:
            limite = Decimal(limite_texto)
            if limite <= 0:
                raise InvalidOperation
        except InvalidOperation:
            flash("Informe um limite válido maior que zero.")
            return redirect(url_for("financeiro.cartoes"))

        novo_cartao = Cartao(
            nome=nome,
            limite=limite,
            dia_fechamento=dia_fechamento,
            dia_vencimento=dia_vencimento,
            usuario_id=current_user.id
        )

        db.session.add(novo_cartao)
        db.session.commit()

        flash("Cartão cadastrado com sucesso!")
        return redirect(url_for("financeiro.cartoes"))

    lista_cartoes = Cartao.query.filter_by(usuario_id=current_user.id).all()
    return render_template("cartoes.html", cartoes=lista_cartoes)


@financeiro.route("/cartoes/<int:cartao_id>/excluir", methods=["POST"])
@login_required
def excluir_cartao(cartao_id):
    cartao = Cartao.query.filter_by(id=cartao_id, usuario_id=current_user.id).first_or_404()
    db.session.delete(cartao)
    db.session.commit()
    flash("Cartão excluído com sucesso!")
    return redirect(url_for("financeiro.cartoes"))


@financeiro.route("/metas", methods=["GET", "POST"])
@login_required
def metas():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        objetivo_texto = request.form.get("valor_objetivo", "").strip().replace(",", ".")
        atual_texto = request.form.get("valor_atual", "0").strip().replace(",", ".")
        prazo_texto = request.form.get("prazo", "").strip()

        if not nome or not objetivo_texto:
            flash("Preencha o nome e o valor objetivo da meta.")
            return redirect(url_for("financeiro.metas"))

        try:
            valor_objetivo = Decimal(objetivo_texto)
            valor_atual = Decimal(atual_texto or "0")
            if valor_objetivo <= 0 or valor_atual < 0:
                raise InvalidOperation
        except InvalidOperation:
            flash("Informe valores numéricos válidos.")
            return redirect(url_for("financeiro.metas"))

        prazo = None
        if prazo_texto:
            try:
                prazo = datetime.strptime(prazo_texto, "%Y-%m-%d").date()
            except ValueError:
                flash("Data de prazo inválida.")
                return redirect(url_for("financeiro.metas"))

        nova_meta = Meta(
            nome=nome,
            valor_objetivo=valor_objetivo,
            valor_atual=valor_atual,
            prazo=prazo,
            usuario_id=current_user.id
        )

        db.session.add(nova_meta)
        db.session.commit()

        flash("Meta criada com sucesso!")
        return redirect(url_for("financeiro.metas"))

    lista_metas = Meta.query.filter_by(usuario_id=current_user.id).all()
    return render_template("metas.html", metas=lista_metas)


@financeiro.route("/metas/<int:meta_id>/depositar", methods=["POST"])
@login_required
def depositar_meta(meta_id):
    meta = Meta.query.filter_by(id=meta_id, usuario_id=current_user.id).first_or_404()
    valor_texto = request.form.get("valor", "").strip().replace(",", ".")

    try:
        valor = Decimal(valor_texto)
        if valor <= 0:
            raise InvalidOperation
    except InvalidOperation:
        flash("Informe um valor válido maior que zero para adicionar à meta.")
        return redirect(url_for("financeiro.metas"))

    meta.valor_atual += valor
    db.session.commit()

    flash(f"R$ {valor:.2f} adicionados à meta '{meta.nome}'!")
    return redirect(url_for("financeiro.metas"))


@financeiro.route("/metas/<int:meta_id>/editar", methods=["GET", "POST"])
@login_required
def editar_meta(meta_id):
    meta = Meta.query.filter_by(id=meta_id, usuario_id=current_user.id).first_or_404()

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        objetivo_texto = request.form.get("valor_objetivo", "").strip().replace(",", ".")
        atual_texto = request.form.get("valor_atual", "0").strip().replace(",", ".")
        prazo_texto = request.form.get("prazo", "").strip()

        if not nome or not objetivo_texto:
            flash("Preencha o nome e o valor objetivo.")
            return redirect(url_for("financeiro.editar_meta", meta_id=meta.id))

        try:
            valor_objetivo = Decimal(objetivo_texto)
            valor_atual = Decimal(atual_texto or "0")
            if valor_objetivo <= 0 or valor_atual < 0:
                raise InvalidOperation
        except InvalidOperation:
            flash("Valores numéricos inválidos.")
            return redirect(url_for("financeiro.editar_meta", meta_id=meta.id))

        prazo = None
        if prazo_texto:
            try:
                prazo = datetime.strptime(prazo_texto, "%Y-%m-%d").date()
            except ValueError:
                flash("Data inválida.")
                return redirect(url_for("financeiro.editar_meta", meta_id=meta.id))

        meta.nome = nome
        meta.valor_objetivo = valor_objetivo
        meta.valor_atual = valor_atual
        meta.prazo = prazo

        db.session.commit()
        flash("Meta atualizada com sucesso!")
        return redirect(url_for("financeiro.metas"))

    return render_template("editar_meta.html", meta=meta)


@financeiro.route("/metas/<int:meta_id>/excluir", methods=["POST"])
@login_required
def excluir_meta(meta_id):
    meta = Meta.query.filter_by(id=meta_id, usuario_id=current_user.id).first_or_404()
    db.session.delete(meta)
    db.session.commit()
    flash("Meta excluída com sucesso!")
    return redirect(url_for("financeiro.metas"))