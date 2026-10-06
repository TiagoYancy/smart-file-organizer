# Smart File Organizer

Organiza arquivos por **contexto semântico**, não apenas por extensão. Usa IA local (Ollama) para analisar o conteúdo de imagens e documentos e agrupar arquivos semanticamente similares.

## Características

- 🧠 **Análise semântica**: Usa modelos de visão (LLaVA) para entender o que imagens retratam
- 📁 **Categorias inteligentes**: Agrupa fotos de família juntas (mesmo formatos diferentes), separa memes, screenshots, documentos fiscais, etc.
- 🔧 **Configurável**: JSON personalizável para categorias, subpastas e palavras-chave
- 🛡️ **Seguro**: Dry-run por padrão, detecta duplicatas por hash SHA-256
- 🏠 **Local**: Roda 100% offline com Ollama (LGPD compliant)

## Instalação

```bash
# 1. Instalar Ollama (se não tiver)
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Baixar modelo de visão
ollama pull llava:latest

# 3. Instalar dependências Python
pip install -r requirements.txt
```

## Uso

```bash
# Simulação (dry-run) - mostra o que seria feito
python smart_organize.py ~/Downloads

# Executa de verdade
python smart_organize.py ~/Downloads --apply

# Com config personalizada
python smart_organize.py ~/Downloads --config meu_config.json --apply

# Verificar dependências
python smart_organize.py --doctor

# Salvar config padrão para personalizar
python smart_organize.py ~/Downloads --save-config meu_config.json
```

## Exemplo de organização

**Antes:**
```
Downloads/
├── foto_familia.png
├── meme_engracado.jpg
├── foto_casamento.jpeg
├── nota_fiscal.pdf
├── curriculo.docx
└── video_youtube.mp4
```

**Depois (com --apply):**
```
Downloads/
├── fotos/
│   ├── familia/
│   │   ├── foto_familia.png
│   │   └── foto_casamento.jpeg
│   ├── eventos/
│   │   └── foto_casamento.jpeg
│   └── documentos_foto/
│       └── nota_fiscal.pdf  (se for foto de nota)
├── imagens_web/
│   ├── memes/
│   │   └── meme_engracado.jpg
│   └── capturas_tela/
├── documentos/
│   ├── pessoais/
│   │   └── curriculo.docx
│   └── financeiros/
│       └── nota_fiscal.pdf
└── videos/
    └── downloads/
        └── video_youtube.mp4
```

## Como funciona a lógica semântica

1. **Classificação por formato**: Primeiro identifica a categoria base (foto, vídeo, documento, etc.)
2. **Análise de conteúdo**: Para imagens, usa LLaVA via Ollama para "ver" o que a imagem retrata
3. **Subcategorização**: Combina formato + semântica para criar pastas específicas:
   - `fotos/familia/` = imagens que retratam pessoas/família (qualquer formato)
   - `fotos/paisagens/` = imagens de natureza/cenários
   - `imagens_web/memes/` = imagens de humor da internet
   - `documentos/financeiros/` = notas fiscais, boletos, extratos
   - etc.

## Configuração personalizada

Edite `config/default_config.json` ou crie seu próprio JSON com estrutura:

```json
{
  "minha_categoria": {
    "name": "minha_categoria",
    "extensions": [".ext1", ".ext2"],
    "mime_prefixes": ["image/", "application/"],
    "keywords": ["palavra1", "palavra2"],
    "subcategories": {
      "subpasta1": ["keyword1", "keyword2"],
      "subpasta2": ["keyword3"]
    }
  }
}
```

## Requisitos

- Python 3.10+
- Ollama rodando localmente (`ollama serve`)
- Modelo de visão: `llava:latest` (ou `llava:13b`, `llava:34b`)
- 4GB+ RAM para modelo 7B, 8GB+ para 13B

## Licença

MIT