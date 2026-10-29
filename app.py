import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, send_from_directory

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=BASE, static_url_path='')

ARQUIVO_DB = os.path.join(BASE, 'cautelas.db')


def conectar():
    conn = sqlite3.connect(ARQUIVO_DB)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_banco():
    try:
        conn = conectar()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cautelas (
                id TEXT PRIMARY KEY,
                dados TEXT NOT NULL,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ Banco SQLite inicializado:", ARQUIVO_DB)
    except Exception as e:
        print("⚠️  Aviso ao inicializar banco:", e)


def ler_html(nome):
    caminho = os.path.join(BASE, nome)
    with open(caminho, 'r', encoding='utf-8') as f:
        return f.read()


@app.route('/')
def intro():
    return render_template_string(ler_html('index.html'))


@app.route('/dashboard')
def dashboard():
    return render_template_string(ler_html('dashboard.html'))


@app.route('/1cia.png')
def logo():
    return send_from_directory(BASE, '1cia.png')


@app.route('/api/cautelas', methods=['GET'])
def listar():
    try:
        conn = conectar()
        rows = conn.execute('SELECT dados FROM cautelas ORDER BY criado_em DESC').fetchall()
        conn.close()
        return jsonify([json.loads(r['dados']) for r in rows])
    except Exception as e:
        print('ERRO listar:', e)
        return jsonify({'erro': str(e)}), 500


@app.route('/api/cautelas', methods=['POST'])
def criar():
    nova = request.get_json()
    if not nova:
        return jsonify({'erro': 'Dados inválidos'}), 400
    try:
        nova['id'] = nova.get('id') or (
            str(int(datetime.now().timestamp() * 1000)) + '-' + os.urandom(3).hex()
        )
        nova['criadoEm'] = nova.get('criadoEm') or datetime.now().isoformat()
        conn = conectar()
        conn.execute(
            'INSERT INTO cautelas (id, dados) VALUES (?, ?)',
            (nova['id'], json.dumps(nova, ensure_ascii=False))
        )
        conn.commit()
        conn.close()
        return jsonify(nova), 201
    except Exception as e:
        print('ERRO criar:', e)
        return jsonify({'erro': str(e)}), 500


@app.route('/api/cautelas/<cautela_id>/devolucao', methods=['PUT'])
def devolver(cautela_id):
    dados_dev = request.get_json()
    if not dados_dev:
        return jsonify({'erro': 'Dados inválidos'}), 400
    try:
        conn = conectar()
        row = conn.execute('SELECT dados FROM cautelas WHERE id = ?', (cautela_id,)).fetchone()
        if not row:
            conn.close()
            return jsonify({'erro': 'Cautela não encontrada'}), 404
        c = json.loads(row['dados'])
        c['status'] = 'devolvida'
        c['devolucao'] = dados_dev
        conn.execute(
            'UPDATE cautelas SET dados = ? WHERE id = ?',
            (json.dumps(c, ensure_ascii=False), cautela_id)
        )
        conn.commit()
        conn.close()
        return jsonify(c)
    except Exception as e:
        print('ERRO devolver:', e)
        return jsonify({'erro': str(e)}), 500


@app.route('/api/backup', methods=['GET'])
def backup():
    try:
        conn = conectar()
        rows = conn.execute('SELECT dados FROM cautelas').fetchall()
        conn.close()
        lista = [json.loads(r['dados']) for r in rows]
        data_str = datetime.now().strftime('%Y-%m-%d_%H-%M')
        return (
            json.dumps(lista, ensure_ascii=False, indent=2),
            200,
            {
                'Content-Type': 'application/json; charset=utf-8',
                'Content-Disposition': f'attachment; filename="backup_cautelas_{data_str}.json"'
            }
        )
    except Exception as e:
        print('ERRO backup:', e)
        return jsonify({'erro': str(e)}), 500


@app.route('/api/backup', methods=['POST'])
def importar_backup():
    dados = request.get_json()
    if not isinstance(dados, list):
        return jsonify({'erro': 'Formato inválido'}), 400
    modo = request.args.get('modo', 'substituir')
    try:
        conn = conectar()
        if modo == 'substituir':
            conn.execute('DELETE FROM cautelas')
            for c in dados:
                c['id'] = c.get('id') or (
                    str(int(datetime.now().timestamp() * 1000)) + '-' + os.urandom(3).hex()
                )
                conn.execute(
                    'INSERT INTO cautelas (id, dados) VALUES (?, ?)',
                    (c['id'], json.dumps(c, ensure_ascii=False))
                )
        else:
            existentes = {r['id'] for r in conn.execute('SELECT id FROM cautelas').fetchall()}
            for c in dados:
                if c.get('id') and c['id'] not in existentes:
                    conn.execute(
                        'INSERT INTO cautelas (id, dados) VALUES (?, ?)',
                        (c['id'], json.dumps(c, ensure_ascii=False))
                    )
        conn.commit()
        conn.close()
        return jsonify({'ok': True, 'total': len(dados)})
    except Exception as e:
        print('ERRO importar:', e)
        return jsonify({'erro': str(e)}), 500


inicializar_banco()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)