Здесь процедуры, вызываемые методом https://api.blagodarie.org/api/update-frontend-site/.
Метод же вызывается github'ом при любом коммите в ветке master или dev-site.
В зависимости от того, из какой ветки коммит, master или dev-site, метод выполняет
процедуру в соответствующей папке.

Действия процедуры, на примере master/update.sh, версии prod благодари.рф:

(ниже ... : /home/www-data/blagodari.rf.busted)

    - обновляет git репозиторий в .../git/prod
    - копирует оттуда blagodarie в .../busted/prod/blagodarie
    - из каталога .../busted запускает
        grunt "cacheBust:prod"
      тем самым в .../busted/prod/blagodarie
      в index.html's изменяются линки на js/css, например,

      <script src="settings.js"></script> заменяется на
      <script src="settings.e8fa8ead84442467.js"></script>
      где e8fa8ead84442467 - md5 hash содержимого settings.js
      
    - переименовывает:
        .../busted/prod/blagodarie в 
        .../busted/prod/<время>
    - изменяет soft-link .../link/prod, чтоб указывал
      на .../busted/prod/<время>
      
    - старые .../busted/prod/<время>, те у которых время меньше, удаляются
      процедурой /busted/leave_only.pl <время>
    
    Поскольку в описании prod- виртуального хоста апача, /etc/apache2/sites-enabled/blagodari.rf.conf
    documentRoot указывает на .../.../link/prod, то сейчас содержимое
    https://благодари.рф будет браться из .../.../busted/prod/<время>,
    там все ссылки на js/css файлы изменены и клиентский браузер будет вынужден их перечитать
    
    В описании prod- виртуального хоста апача, /etc/apache2/sites-enabled/blagodari.rf.conf
    также указано, чтоб при обращении к js/css файлу с именем, например, settings.e8fa8ead84442467.js,
    в клиентский браузер отдавалось содержимое settings.js

    
