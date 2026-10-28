import json
import os
import threading
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, send_from_directory

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=BASE, static_url_path="")
LOCK = threading.Lock()

# Vercel's deployment directory is read-only. /tmp is writable but temporary:
# data can disappear on cold starts and is not shared between instances.
ARQUIVO_INICIAL = os.path.join(BASE, "cautelas.json")
ARQUIVO_DADOS = os.path.join("/tmp", "enc_mat_1cia_cautelas.json")


def garantir_arquivo_dados():
    if not os.path.exists(ARQUIVO_DADOS):
        try:
            with open(ARQUIVO_INICIAL, "r", encoding="utf-8") as origem:
                dados = json.load(origem)
            if not isinstance(dados, list):
                dados = []
        except (OSError, json.JSONDecodeError):
            dados = []
        with open(ARQUIVO_DADOS, "w", encoding="utf-8") as destino:
            json.dump(dados, destino, ensure_ascii=False, indent=2)


def carregar_cautelas():
    garantir_arquivo_dados()
    try:
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            dados = json.load(f)
        return dados if isinstance(dados, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def salvar_cautelas(cautelas):
    garantir_arquivo_dados()
    temporario = ARQUIVO_DADOS + ".tmp"
    with open(temporario, "w", encoding="utf-8") as f:
        json.dump(cautelas, f, ensure_ascii=False, indent=2)
    os.replace(temporario, ARQUIVO_DADOS)


def ler_html(nome):
    caminho = os.path.join(BASE, nome)
    with open(caminho, "r", encoding="utf-8") as f:
        return f.read()


@app.route("/")
def intro():
    return render_template_string(ler_html("index.html"))


@app.route("/dashboard")
def dashboard():
    return render_template_string(ler_html("dashboard.html"))


@app.route("/1cia.png")
def logo():
    return send_from_directory(BASE, "1cia.png")


@app.route("/api/cautelas", methods=["GET"])
def listar():
    with LOCK:
        return jsonify(carregar_cautelas())


@app.route("/api/cautelas", methods=["POST"])
def criar():
    nova = request.get_json(silent=True)
    if not isinstance(nova, dict) or not nova:
        return jsonify({"erro": "Dados inválidos"}), 400
    with LOCK:
        cautelas = carregar_cautelas()
        nova["id"] = nova.get("id") or (
            str(int(datetime.now().timestamp() * 1000)) + "-" + os.urandom(3).hex()
        )
        nova["criadoEm"] = nova.get("criadoEm") or datetime.now().isoformat()
        cautelas.insert(0, nova)
        salvar_cautelas(cautelas)
    return jsonify(nova), 201


@app.route("/api/cautelas/<cautela_id>", methods=["DELETE"])
def deletar(cautela_id):
    with LOCK:
        cautelas = carregar_cautelas()
        novas = [c for c in cautelas if c.get("id") != cautela_id]
        if len(novas) == len(cautelas):
            return jsonify({"erro": "Cautela não encontrada"}), 404
        salvar_cautelas(novas)
    return jsonify({"ok": True})


@app.route("/api/cautelas/<cautela_id>/devolucao", methods=["PUT"])
def devolver(cautela_id):
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return jsonify({"erro": "Dados inválidos"}), 400
    with LOCK:
        cautelas = carregar_cautelas()
        for cautela in cautelas:
            if cautela.get("id") == cautela_id:
                cautela["status"] = "devolvida"
                cautela["devolucao"] = dados
                salvar_cautelas(cautelas)
                return jsonify(cautela)
    return jsonify({"erro": "Cautela não encontrada"}), 404


@app.route("/api/backup", methods=["GET"])
def backup():
    with LOCK:
        cautelas = carregar_cautelas()
    data_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    return (
        json.dumps(cautelas, ensure_ascii=False, indent=2),
        200,
        {
            "Content-Type": "application/json; charset=utf-8",
            "Content-Disposition": f'attachment; filename="backup_cautelas_{data_str}.json"',
        },
    )


@app.route("/api/backup", methods=["POST"])
def importar_backup():
    dados = request.get_json(silent=True)
    if not isinstance(dados, list):
        return jsonify({"erro": "Formato inválido"}), 400
    modo = request.args.get("modo", "substituir")
    with LOCK:
        if modo == "mesclar":
            atuais = carregar_cautelas()
            ids_atuais = {c.get("id") for c in atuais}
            novas = [c for c in dados if c.get("id") not in ids_atuais]
            todas = novas + atuais
        else:
            todas = dados
        salvar_cautelas(todas)
    return jsonify({"ok": True, "total": len(todas)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
