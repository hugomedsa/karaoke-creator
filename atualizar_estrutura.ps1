# Arquivo de saída
$out = "estrutura_projeto.txt"
if (Test-Path $out) { Remove-Item $out }

# Função para mostrar estrutura de diretórios (similar ao tree)
function Show-DirectoryTree {
    param([string]$Path = ".", [int]$IndentLevel = 0)
    
    $indent = "|   " * $IndentLevel
    $items = Get-ChildItem -Path $Path -Exclude venv | Sort-Object Name
    
    foreach ($item in $items) {
        if ($item.Name -eq "venv") { continue }
        
        if ($item.PSIsContainer) {
            Add-Content $out "$indent|-- [$($item.Name)]/"
            Show-DirectoryTree -Path $item.FullName -IndentLevel ($IndentLevel + 1)
        } else {
            Add-Content $out "$indent|-- $($item.Name)"
        }
    }
}

# ---------- 1) Estrutura do projeto ----------
Add-Content $out "============================================"
Add-Content $out "ESTRUTURA DO PROJETO"
Add-Content $out "============================================`n"

Show-DirectoryTree -Path "."

Add-Content $out "`n`n============================================"
Add-Content $out "CONTEÚDO DOS ARQUIVOS (.py e .txt)"
Add-Content $out "============================================`n"

# ---------- 2) Conteúdo dos arquivos .py e .txt (exceto venv) ----------
Get-ChildItem -Path . -Include *.py, *.txt -Recurse -File |
    Where-Object { $_.FullName -notmatch '\\venv\\.*' } |
    Sort-Object FullName |
    ForEach-Object {
        Add-Content $out "`n" + ("=" * 60)
        Add-Content $out "ARQUIVO: $($_.FullName)"
        Add-Content $out ("=" * 60) + "`n"
        
        try {
            $content = Get-Content $_.FullName -ErrorAction Stop
            if ($content) {
                Add-Content $out $content
            } else {
                Add-Content $out "[ARQUIVO VAZIO]"
            }
        } catch {
            Add-Content $out "[ERRO AO LER ARQUIVO: $($_.Exception.Message)]"
        }
    }

Write-Host "Arquivo gerado: $out" -ForegroundColor Green