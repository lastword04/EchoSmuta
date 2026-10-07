import fs from 'fs';
import path from 'path';

// Читаем размеры GIF из заголовков файлов в public/images/bells
const ROOT = 'public/images/bells';
const OUT = 'public/bells-sizes.json';

const result = {};

fs.readdirSync(ROOT).forEach((folder) => {
    const fdir = path.join(ROOT, folder);
    if (!fs.statSync(fdir).isDirectory()) return;

    fs.readdirSync(fdir).forEach((fn) => {
        if (!fn.toLowerCase().endsWith('.gif')) return;

        const code = fn.slice(0, -4);
        const buffer = fs.readFileSync(path.join(fdir, fn));

        // Проверяем сигнатуру "GIF" и читаем ширину/высоту из заголовка
        if (buffer.length < 10) return;
        if (buffer[0] !== 0x47 || buffer[1] !== 0x49 || buffer[2] !== 0x46) return;

        const w = buffer.readUInt16LE(6);
        const h = buffer.readUInt16LE(8);
        result[code] = [w, h];
    });
});

fs.writeFileSync(OUT, JSON.stringify(result));
console.log(`OK: ${Object.keys(result).length} смайликов -> ${OUT}`);