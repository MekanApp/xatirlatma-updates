# Xatirlatma Sistemi — yeniləmə repozitoriyası

Bu qovluğun məzmunu GitHub-da **yeni public repo**ya yüklənir (məs. `xatirlatma-updates`).
Burada yalnız imzalı modullar var; gizli heç nə yoxdur.

## Bir dəfəlik quraşdırma
1. github.com-da yeni **Public** repo yaradın (məs. `xatirlatma-updates`).
2. Bu qovluqda:
   ```
   git init
   git add .
   git commit -m "ilk"
   git branch -M main
   git remote add origin https://github.com/ISTIFADECI/xatirlatma-updates.git
   git push -u origin main
   ```
3. `alarm_sistemi\version.py` faylında yazın:
   `UPDATE_BASE_URL = "https://raw.githubusercontent.com/ISTIFADECI/xatirlatma-updates/main/"`
   və proqramı yenidən build edin.

## Hər yeniləmədə
1. `modules\` içindəki faylı dəyişin.
2. `vendor_tools\release_update.bat` işlədin (manifest.json imzalanır).
3. `git add . && git commit -m "yenilik" && git push`
Proqram açılanda və Parametrlər-dən "Yeniləməni yoxla" ilə özü yüklənir.

Token lazım deyil: bütün fayllar imzalıdır, saxta fayl proqram tərəfindən rədd edilir.
