#!/usr/bin/env python3
"""
Smart File Organizer - Organizes files by semantic context, not just extension.
Uses local LLMs (Ollama) to understand file content and group semantically similar files.
"""

import argparse
import hashlib
import json
import mimetypes
import os
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


@dataclass
class FileInfo:
    path: Path
    mime_type: str
    size: int
    hash: str
    metadata: dict = field(default_factory=dict)
    semantic_tags: list = field(default_factory=list)
    suggested_category: str = ""


@dataclass
class CategoryConfig:
    name: str
    extensions: list = field(default_factory=list)
    mime_prefixes: list = field(default_factory=list)
    keywords: list = field(default_factory=list)
    subcategories: dict = field(default_factory=dict)


class SmartFileOrganizer:
    DEFAULT_CATEGORIES = {
        "fotos": CategoryConfig(
            name="fotos",
            extensions=[".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic", ".raw", ".cr2", ".nef", ".tiff", ".tif"],
            mime_prefixes=["image/"],
            keywords=["foto", "photograph", "picture", "família", "family", "retrato", "paisagem", "landscape", "selfie"],
            subcategories={
                "familia": ["família", "family", "retrato", "portrait", "pessoas", "people", "selfie", "grupo", "group"],
                "paisagens": ["paisagem", "landscape", "natureza", "nature", "cenário", "scenery", "praia", "beach", "montanha", "mountain", "cidade", "city"],
                "eventos": ["evento", "event", "festa", "party", "casamento", "wedding", "aniversário", "birthday", "formatura", "graduation", "batizado"],
                "documentos_foto": ["documento", "document", "recibo", "receipt", "nota", "nota fiscal", "invoice", "rg", "cpf", "cnh", "passaporte"],
                "prints_tela": ["print", "screenshot", "captura", "screen", "tela"],
                "outros": []
            }
        ),
        "videos": CategoryConfig(
            name="videos",
            extensions=[".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv", ".m4v", ".3gp", ".ts", ".mts"],
            mime_prefixes=["video/"],
            keywords=["vídeo", "video", "filmagem", "recording", "clipe", "clip"],
            subcategories={
                "familia": ["família", "family", "caseiro", "home", "criança", "child", "bebê", "baby"],
                "trabalho": ["trabalho", "work", "reunião", "meeting", "apresentação", "presentation", "treinamento", "training"],
                "downloads": ["download", "youtube", "tiktok", "reels", "shorts", "instagram", "facebook", "twitter", "x.com"],
                "cursos": ["curso", "course", "aula", "lesson", "tutorial", "webinar"],
                "outros": []
            }
        ),
        "documentos": CategoryConfig(
            name="documentos",
            extensions=[".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".md", ".tex", ".pages", ".epub"],
            mime_prefixes=["application/pdf", "application/msword", "application/vnd.openxmlformats", "application/epub"],
            keywords=["documento", "document", "texto", "text", "contrato", "contract", "relatório", "report", "artigo", "article"],
            subcategories={
                "pessoais": ["pessoal", "personal", "currículo", "resume", "cv", "certidão", "certificate", "identidade", "rg", "cpf", "passaporte", "carteira"],
                "trabalho": ["trabalho", "work", "contrato", "contract", "relatório", "report", "projeto", "project", "proposta", "proposal", "apresentação", "presentation"],
                "financeiros": ["financeiro", "financial", "banco", "bank", "fatura", "invoice", "recibo", "receipt", "nota fiscal", "nf", "imposto", "tax", "irpf", "declaração", "boleto", "comprovante"],
                "estudos": ["estudo", "study", "curso", "course", "aula", "lesson", "livro", "book", "artigo", "article", "paper", "tese", "thesis", "dissertação", "monografia", "apostila"],
                "juridicos": ["jurídico", "legal", "processo", "lawsuit", "petição", "contrato", "termo", "procuração", "escritura"],
                "medicos": ["médico", "medical", "exame", "exam", "laudo", "receita", "prescrição", "vacina", "carteira vacinação"],
                "outros": []
            }
        ),
        "audio": CategoryConfig(
            name="audio",
            extensions=[".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".opus", ".aiff", ".alac"],
            mime_prefixes=["audio/"],
            keywords=["áudio", "audio", "música", "music", "som", "sound", "gravação", "recording", "podcast"],
            subcategories={
                "musica": ["música", "music", "song", "álbum", "album", "artista", "artist", "playlist"],
                "podcasts": ["podcast", "episode", "episódio", "programa", "show"],
                "gravacoes": ["gravação", "recording", "voice", "voz", "memo", "whatsapp", "audio", "áudio"],
                "audiobooks": ["audiobook", "audio book", "livro audio", "audiolivro"],
                "outros": []
            }
        ),
        "imagens_web": CategoryConfig(
            name="imagens_web",
            extensions=[".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"],
            mime_prefixes=["image/"],
            keywords=["meme", "internet", "web", "download", "reddit", "twitter", "instagram", "whatsapp", "forwarded", "encaminhado", "received", "sticker", "figurinha"],
            subcategories={
                "memes": ["meme", "engraçado", "funny", "humor", "piada", "joke"],
                "capturas_tela": ["captura", "screenshot", "screen", "print", "tela"],
                "encaminhados": ["encaminhado", "forwarded", "received", "whatsapp", "telegram", "compartilhado", "shared"],
                "stickers": ["sticker", "figurinha", "adesivo"],
                "outros": []
            }
        ),
        "codigo": CategoryConfig(
            name="codigo",
            extensions=[".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h", ".go", ".rs", ".rb", ".php", ".html", ".css", ".scss", ".json", ".yaml", ".yml", ".toml", ".sql", ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd", ".dockerfile", ".dockerignore", ".gitignore", ".env", ".ini", ".cfg", ".conf", ".xml", ".csv"],
            mime_prefixes=["text/x-", "application/json", "text/csv"],
            keywords=["código", "code", "script", "programa", "source", "src"],
            subcategories={
                "python": [".py", ".pyw", ".pyi"],
                "javascript_typescript": [".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"],
                "web_frontend": [".html", ".css", ".scss", ".sass", ".less", ".vue", ".svelte"],
                "backend": [".java", ".go", ".rs", ".rb", ".php", ".cs", ".vb"],
                "config_data": [".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".xml", ".csv", ".env"],
                "scripts_shell": [".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd"],
                "docker": ["dockerfile", ".dockerignore", "docker-compose"],
                "git": [".gitignore", ".gitattributes", ".gitmodules"],
                "outros": []
            }
        ),
        "arquivos_compactados": CategoryConfig(
            name="arquivos_compactados",
            extensions=[".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".tgz", ".tbz2", ".txz", ".zst"],
            mime_prefixes=["application/zip", "application/x-rar", "application/x-7z", "application/x-tar", "application/gzip", "application/x-bzip2", "application/x-xz", "application/zstd"],
            keywords=["compactado", "archive", "backup", "comprimido"],
            subcategories={
                "backups": ["backup", "bak", "restore"],
                "projetos": ["projeto", "project", "source", "src"],
                "downloads": ["download"],
                "outros": []
            }
        ),
        "executaveis": CategoryConfig(
            name="executaveis",
            extensions=[".exe", ".msi", ".app", ".dmg", ".pkg", ".deb", ".rpm", ".apk", ".bin", ".run", ".appimage", ".flatpak", ".snap"],
            mime_prefixes=["application/x-executable", "application/vnd.android", "application/x-msdownload", "application/x-apple-diskimage", "application/x-msdos-program"],
            keywords=["instalador", "installer", "executável", "executable", "programa", "setup"],
            subcategories={
                "windows": [".exe", ".msi"],
                "macos": [".dmg", ".pkg", ".app"],
                "linux": [".deb", ".rpm", ".appimage", ".flatpak", ".snap", ".bin", ".run"],
                "android": [".apk"],
                "outros": []
            }
        ),
        "imagens_3d_design": CategoryConfig(
            name="imagens_3d_design",
            extensions=[".blend", ".obj", ".fbx", ".gltf", ".glb", ".stl", ".ply", ".dae", ".3ds", ".max", ".c4d", ".ma", ".mb", ".psd", ".ai", ".eps", ".indd", ".xd", ".fig", ".sketch"],
            mime_prefixes=["application/octet-stream", "image/vnd.adobe"],
            keywords=["3d", "modelo", "model", "design", "blender", "photoshop", "illustrator", "figma", "sketch"],
            subcategories={
                "modelos_3d": [".blend", ".obj", ".fbx", ".gltf", ".glb", ".stl", ".ply", ".dae", ".3ds", ".max", ".c4d", ".ma", ".mb"],
                "design_psd": [".psd", ".psb"],
                "vetores": [".ai", ".eps", ".svg"],
                "layout": [".indd", ".xd", ".fig", ".sketch"],
                "outros": []
            }
        ),
        "banco_dados": CategoryConfig(
            name="banco_dados",
            extensions=[".sql", ".sqlite", ".db", ".sqlite3", ".mdb", ".accdb", ".dbf", ".frm", ".ibd", ".myd", ".myi"],
            mime_prefixes=["application/x-sqlite3", "application/vnd.sqlite3"],
            keywords=["banco", "database", "db", "sql", "dados", "data"],
            subcategories={
                "sqlite": [".sqlite", ".sqlite3", ".db"],
                "mysql": [".frm", ".ibd", ".myd", ".myi"],
                "access": [".mdb", ".accdb"],
                "scripts_sql": [".sql"],
                "outros": []
            }
        ),
        "fontes": CategoryConfig(
            name="fontes",
            extensions=[".ttf", ".otf", ".woff", ".woff2", ".eot", ".fon", ".pfb", ".pfm"],
            mime_prefixes=["font/", "application/font-"],
            keywords=["fonte", "font", "tipo", "typeface", "typography"],
            subcategories={
                "truetype": [".ttf", ".ttc"],
                "opentype": [".otf"],
                "web": [".woff", ".woff2", ".eot"],
                "outros": []
            }
        ),
        "outros": CategoryConfig(
            name="outros",
            extensions=[],
            mime_prefixes=[],
            keywords=[],
            subcategories={}
        )
    }

    def __init__(self, source_dir: Path, config_path: Optional[Path] = None, dry_run: bool = True, ollama_model: str = "llava:latest"):
        self.source_dir = Path(source_dir).resolve()
        self.config_path = config_path
        self.dry_run = dry_run
        self.ollama_model = ollama_model
        self.categories = self.DEFAULT_CATEGORIES.copy()
        self.load_custom_config()
        self.files: list[FileInfo] = []
        self.plan: dict = {}

    def load_custom_config(self):
        if self.config_path and self.config_path.exists():
            with open(self.config_path) as f:
                custom = json.load(f)
            for name, cfg in custom.items():
                if name in self.categories:
                    self.categories[name] = CategoryConfig(**cfg)
                else:
                    self.categories[name] = CategoryConfig(**cfg)

    def save_custom_config(self, path: Path):
        data = {}
        for name, cfg in self.categories.items():
            data[name] = {
                "name": cfg.name,
                "extensions": cfg.extensions,
                "mime_prefixes": cfg.mime_prefixes,
                "keywords": cfg.keywords,
                "subcategories": cfg.subcategories
            }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_file_hash(self, path: Path) -> str:
        hasher = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()[:16]

    def detect_mime_type(self, path: Path) -> str:
        mime, _ = mimetypes.guess_type(str(path))
        return mime or "application/octet-stream"

    def scan_files(self) -> list[FileInfo]:
        files = []
        for path in self.source_dir.rglob('*'):
            if path.is_file() and not path.name.startswith('.'):
                mime = self.detect_mime_type(path)
                fhash = self.get_file_hash(path)
                files.append(FileInfo(
                    path=path,
                    mime_type=mime,
                    size=path.stat().st_size,
                    hash=fhash
                ))
        self.files = files
        return files

    def analyze_image_with_ollama(self, path: Path) -> dict:
        if not OLLAMA_AVAILABLE:
            return {"tags": [], "description": "Ollama not available"}

        try:
            response = ollama.chat(
                model=self.ollama_model,
                messages=[{
                    "role": "user",
                    "content": "Analise esta imagem e retorne apenas um JSON com: tags (lista de palavras-chave em português descrevendo o conteúdo), description (descrição curta em português), category_suggestion (categoria sugerida: familia, paisagens, eventos, documentos_foto, memes, capturas_tela, encaminhados, outros). Seja conciso.",
                    "images": [str(path)]
                }],
                options={"temperature": 0.1}
            )
            content = response['message']['content']
            # Try to parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"tags": [], "description": content, "category_suggestion": "outros"}
        except Exception as e:
            return {"tags": [], "description": f"Error: {e}", "category_suggestion": "outros"}

    def extract_text_content(self, path: Path) -> str:
        """Extract text content from text-based files for analysis."""
        try:
            if path.suffix.lower() in ['.txt', '.md', '.py', '.js', '.json', '.yaml', '.yml', '.html', '.css', '.sql', '.sh']:
                return path.read_text(encoding='utf-8', errors='ignore')[:5000]
        except Exception:
            pass
        return ""

    def analyze_document_with_ollama(self, path: Path) -> dict:
        if not OLLAMA_AVAILABLE:
            return {"tags": [], "category_suggestion": "outros"}

        text = self.extract_text_content(path)
        if not text:
            return {"tags": [], "category_suggestion": "outros"}

        try:
            response = ollama.chat(
                model=self.ollama_model.replace('llava', 'llama3.2').replace('llava:latest', 'llama3.2:latest'),
                messages=[{
                    "role": "user",
                    "content": f"Analise este texto e retorne JSON com: tags (palavras-chave em português), category_suggestion (pessoais, trabalho, financeiros, estudos, outros). Texto: {text[:3000]}"
                }],
                options={"temperature": 0.1}
            )
            content = response['message']['content']
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
        return {"tags": [], "category_suggestion": "outros"}

    def analyze_file(self, file_info: FileInfo) -> FileInfo:
        mime = file_info.mime_type
        path = file_info.path

        # Determine main category by extension/mime
        main_category = self.categorize_by_format(file_info)
        file_info.metadata['main_category'] = main_category

        # Analyze content for semantic tags
        if mime.startswith('image/') and OLLAMA_AVAILABLE:
            result = self.analyze_image_with_ollama(path)
            file_info.semantic_tags = result.get('tags', [])
            file_info.metadata['description'] = result.get('description', '')
            subcat = result.get('category_suggestion', 'outros')
            file_info.metadata['subcategory'] = subcat
        elif mime.startswith('text/') or path.suffix.lower() in ['.pdf', '.doc', '.docx'] and OLLAMA_AVAILABLE:
            result = self.analyze_document_with_ollama(path)
            file_info.semantic_tags = result.get('tags', [])
            file_info.metadata['subcategory'] = result.get('category_suggestion', 'outros')

        # Determine suggested category combining format + semantics
        file_info.suggested_category = self.determine_final_category(file_info)

        return file_info

    def categorize_by_format(self, file_info: FileInfo) -> str:
        ext = file_info.path.suffix.lower()
        mime = file_info.mime_type

        for cat_name, cat_config in self.categories.items():
            if ext in cat_config.extensions:
                return cat_name
            for prefix in cat_config.mime_prefixes:
                if mime.startswith(prefix):
                    return cat_name
        return "outros"

    def determine_final_category(self, file_info: FileInfo) -> str:
        main_cat = file_info.metadata.get('main_category', 'outros')
        subcat = file_info.metadata.get('subcategory', 'outros')

        # If we have semantic subcategory, use it to create a more specific path
        if main_cat in self.categories and subcat in self.categories[main_cat].subcategories:
            return f"{main_cat}/{subcat}"

        # Check keywords in filename
        filename = file_info.path.name.lower()
        for cat_name, cat_config in self.categories.items():
            for keyword in cat_config.keywords:
                if keyword.lower() in filename:
                    return cat_name

        return main_cat

    def analyze_all_files(self):
        print(f"Analisando {len(self.files)} arquivos...")
        for i, file_info in enumerate(self.files, 1):
            print(f"  [{i}/{len(self.files)}] {file_info.path.name}")
            self.analyze_file(file_info)

    def build_plan(self) -> dict:
        plan = {}
        for file_info in self.files:
            target_rel = file_info.suggested_category
            target_dir = self.source_dir / target_rel
            plan.setdefault(str(target_dir), []).append({
                "source": str(file_info.path),
                "filename": file_info.path.name,
                "size": file_info.size,
                "category": file_info.suggested_category,
                "tags": file_info.semantic_tags
            })
        self.plan = plan
        return plan

    def print_plan(self):
        print("\n=== PLANO DE ORGANIZAÇÃO ===")
        if not self.plan:
            print("Nenhum arquivo para organizar.")
            return

        total_files = sum(len(v) for v in self.plan.values())
        print(f"Total: {total_files} arquivos -> {len(self.plan)} pastas de destino\n")

        for target_dir, files in sorted(self.plan.items()):
            rel = Path(target_dir).relative_to(self.source_dir)
            print(f"📁 {rel}/ ({len(files)} arquivos)")
            for f in files:
                tags = f" [{', '.join(f['tags'])}]" if f['tags'] else ""
                print(f"   📄 {f['filename']} ({self.format_size(f['size'])}){tags}")

    def format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"

    def execute_plan(self, confirm: bool = False):
        if self.dry_run and not confirm:
            print("\n⚠️  MODO DRY-RUN (simulação). Use --execute para aplicar.")
            return

        print("\n=== EXECUTANDO ORGANIZAÇÃO ===")
        moved = 0
        errors = 0

        for target_dir, files in self.plan.items():
            Path(target_dir).mkdir(parents=True, exist_ok=True)
            for f in files:
                src = Path(f['source'])
                dst = Path(target_dir) / f['filename']

                # Handle duplicates
                if dst.exists():
                    if self.get_file_hash(src) == self.get_file_hash(dst):
                        print(f"  ⏭️  Pulado (idêntico): {f['filename']}")
                        continue
                    # Rename with counter
                    counter = 1
                    stem, suffix = dst.stem, dst.suffix
                    while dst.exists():
                        dst = dst.with_name(f"{stem}_{counter}{suffix}")
                        counter += 1

                try:
                    shutil.move(str(src), str(dst))
                    print(f"  ✅ Movido: {f['filename']} -> {Path(target_dir).relative_to(self.source_dir)}/{dst.name}")
                    moved += 1
                except Exception as e:
                    print(f"  ❌ Erro movendo {f['filename']}: {e}")
                    errors += 1

        print(f"\n✅ Concluído: {moved} movidos, {errors} erros")

    def run(self, execute: bool = False):
        print(f"🔍 Escaneando: {self.source_dir}")
        self.scan_files()
        print(f"📦 Encontrados: {len(self.files)} arquivos")

        self.analyze_all_files()
        self.build_plan()
        self.print_plan()

        if execute or not self.dry_run:
            self.execute_plan(confirm=True)
        elif self.dry_run:
            print("\n💡 Execute com --apply para aplicar as mudanças.")


def main():
    parser = argparse.ArgumentParser(
        description="Smart File Organizer - Organiza arquivos por contexto semântico",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s ~/Downloads                    # Simula organização (dry-run)
  %(prog)s ~/Downloads --apply            # Executa organização real
  %(prog)s ~/Downloads --config config.json  # Usa config personalizada
  %(prog)s ~/Downloads --model llava:13b   # Usa modelo Ollama específico
        """
    )
    parser.add_argument('source', help='Diretório de origem para organizar')
    parser.add_argument('--config', '-c', help='Arquivo de configuração JSON personalizado')
    parser.add_argument('--apply', '-a', action='store_true', help='Aplica as mudanças (padrão: dry-run)')
    parser.add_argument('--model', '-m', default='llava:latest', help='Modelo Ollama para análise de imagens (padrão: llava:latest)')
    parser.add_argument('--save-config', help='Salva configuração padrão no caminho especificado')
    parser.add_argument('--doctor', action='store_true', help='Verifica dependências e configuração')

    args = parser.parse_args()

    if args.doctor:
        print("=== DOCTOR CHECK ===")
        print(f"Ollama disponível: {'✅' if OLLAMA_AVAILABLE else '❌'}")
        print(f"PIL/Pillow disponível: {'✅' if PIL_AVAILABLE else '❌'}")
        if OLLAMA_AVAILABLE:
            try:
                models = ollama.list()
                print(f"Modelos Ollama: {[m['name'] for m in models['models']]}")
            except Exception as e:
                print(f"Erro conectando ao Ollama: {e}")
        return

    source = Path(args.source).resolve()
    if not source.exists():
        print(f"❌ Diretório não encontrado: {source}")
        sys.exit(1)

    if args.save_config:
        organizer = SmartFileOrganizer(source)
        organizer.save_custom_config(Path(args.save_config))
        print(f"Configuração salva em: {args.save_config}")
        return

    config_path = Path(args.config) if args.config else None
    organizer = SmartFileOrganizer(
        source_dir=source,
        config_path=config_path,
        dry_run=not args.apply,
        ollama_model=args.model
    )
    organizer.run(execute=args.apply)


if __name__ == "__main__":
    main()