#!/bin/bash

# Список папок (задается вручную)
folders=(
    "auth"
    "captcha-service"
    "characters"
    "chat"
    "email"
    "file-storage"
    "forum"
    "mining"
    "users"
    "economy"
)

# Проходим по каждой папке из списка
for folder in "${folders[@]}"; do
    # Проверяем, существует ли папка
    if [ -d "$folder" ]; then
        # Удаляем папку shared, если она существует
        if [ -d "$folder/shared" ]; then
            rm -rf "$folder/shared"
            echo "Удалена папка $folder/shared"
        fi

        # Копируем папку shared из текущей директории в папку из списка
        if [ -d "./shared" ]; then
            cp -r "./shared" "$folder/"
            echo "Скопирована папка shared в $folder/"
        else
            echo "Папка ./shared не найдена, пропускаем копирование для $folder"
        fi
    else
        echo "Папка $folder не существует, пропускаем"
    fi

done
