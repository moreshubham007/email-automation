# Navigate to project root
Set-Location "C:\Users\VM1030\OneDrive\Desktop\gmail saving flask\flask_gmail_app"

# Remove any existing TinyMCE files and templates
Remove-Item -Path "app\static\js\tinymce" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "templates" -Recurse -Force -ErrorAction SilentlyContinue

# Create necessary directories
$baseDir = "app\static\js\tinymce"
$dirs = @(
    "plugins\advlist",
    "plugins\autolink",
    "plugins\lists",
    "plugins\link",
    "plugins\searchreplace",
    "plugins\visualblocks",
    "plugins\fullscreen",
    "themes\silver",
    "models\dom",
    "icons\default",
    "skins\ui\oxide",
    "skins\content\default"
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path "$baseDir\$dir"
}

# Download files
$files = @{
    "tinymce.min.js" = "https://cdnjs.cloudflare.com/ajax/libs/tinymce/6.7.2/tinymce.min.js"
    "plugins\advlist\plugin.min.js" = "https://cdnjs.cloudflare.com/ajax/libs/tinymce/6.7.2/plugins/advlist/plugin.min.js"
    "plugins\autolink\plugin.min.js" = "https://cdnjs.cloudflare.com/ajax/libs/tinymce/6.7.2/plugins/autolink/plugin.min.js"
    "plugins\lists\plugin.min.js" = "https://cdnjs.cloudflare.com/ajax/libs/tinymce/6.7.2/plugins/lists/plugin.min.js"
    "plugins\link\plugin.min.js" = "https://cdnjs.cloudflare.com/ajax/libs/tinymce/6.7.2/plugins/link/plugin.min.js"
    "plugins\searchreplace\plugin.min.js" = "https://cdnjs.cloudflare.com/ajax/libs/tinymce/6.7.2/plugins/searchreplace/plugin.min.js"
    "plugins\visualblocks\plugin.min.js" = "https://cdnjs.cloudflare.com/ajax/libs/tinymce/6.7.2/plugins/visualblocks/plugin.min.js"
    "plugins\fullscreen\plugin.min.js" = "https://cdnjs.cloudflare.com/ajax/libs/tinymce/6.7.2/plugins/fullscreen/plugin.min.js"
    "themes\silver\theme.min.js" = "https://cdnjs.cloudflare.com/ajax/libs/tinymce/6.7.2/themes/silver/theme.min.js"
    "models\dom\model.min.js" = "https://cdnjs.cloudflare.com/ajax/libs/tinymce/6.7.2/models/dom/model.min.js"
    "icons\default\icons.min.js" = "https://cdnjs.cloudflare.com/ajax/libs/tinymce/6.7.2/icons/default/icons.min.js"
    "skins\ui\oxide\skin.min.css" = "https://cdnjs.cloudflare.com/ajax/libs/tinymce/6.7.2/skins/ui/oxide/skin.min.css"
    "skins\ui\oxide\content.min.css" = "https://cdnjs.cloudflare.com/ajax/libs/tinymce/6.7.2/skins/ui/oxide/content.min.css"
    "skins\content\default\content.min.css" = "https://cdnjs.cloudflare.com/ajax/libs/tinymce/6.7.2/skins/content/default/content.min.css"
}

foreach ($file in $files.GetEnumerator()) {
    $outFile = "$baseDir\$($file.Key)"
    Write-Host "Downloading $($file.Key)..."
    try {
        Invoke-WebRequest -Uri $file.Value -OutFile $outFile
        Write-Host "Successfully downloaded $($file.Key)" -ForegroundColor Green
    }
    catch {
        Write-Host "Failed to download $($file.Key): $_" -ForegroundColor Red
    }
}

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "1. Start your Flask application"
Write-Host "2. Visit http://127.0.0.1:5000/template-management"
Write-Host "3. Check browser console for any remaining errors"