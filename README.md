# ENC MAT — 1ª CIA (Vercel)

Projeto Flask preparado para testes na Vercel, mantendo os arquivos visuais originais.

## Publicar pela Vercel

1. Extraia o ZIP.
2. Crie um repositório no GitHub e envie **os arquivos desta pasta na raiz** do repositório.
3. Entre em https://vercel.com/ e escolha **Add New → Project**.
4. Importe o repositório GitHub.
5. Se a Vercel perguntar o framework, selecione **Flask** ou deixe a detecção automática.
6. Não precisa configurar Build Command nem Output Directory manualmente. A dependência está em `requirements.txt`.
7. Clique em **Deploy**.

Depois da publicação, teste:
- `/` — tela de abertura
- `/dashboard` — painel
- `/api/cautelas` — API de cautelas

## Importante sobre o JSON

Esta versão foi configurada para testes: lê `cautelas.json` como dados iniciais e grava alterações em `/tmp/enc_mat_1cia_cautelas.json`.

**O `/tmp` da Vercel é temporário, pode ser apagado e não é compartilhado entre instâncias.** Portanto, cautelas criadas podem desaparecer após reinicializações/novas instâncias. Não use esta versão para dados reais ou como armazenamento oficial.

O arquivo `cautelas.json` foi iniciado vazio para não publicar os dados pessoais/assinaturas que existiam no arquivo original. Faça backup dos dados originais localmente antes de qualquer migração.

## Testar localmente

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abra `http://127.0.0.1:5000`.

## Segurança

O projeto não tem autenticação. Use apenas dados fictícios enquanto estiver publicado publicamente.
