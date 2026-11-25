#!/usr/bin/env python3
"""to_webp.py — переводит картинки (PNG, JPG, BMP, TIFF) в WebP.

Примеры:
  python to_webp.py папка                    все картинки папки -> папка/webp, размер как был
  python to_webp.py папка --max 256          ужать до 256 px по длинной стороне (жетоны)
  python to_webp.py карта.png --cells 42x28  карта под сетку: 42x28 клеток по 70 px = 2940x1960
  python to_webp.py папка -r -o готово -q 85 с подпапками, в папку «готово», качество 85

Исходные файлы не меняются и не удаляются. Нужна библиотека Pillow: pip install pillow
"""
import argparse
import os
import sys

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Нет библиотеки Pillow. Поставь её командой:  pip install pillow")

EXT = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")


def parse_pair(text, what):
    try:
        a, b = text.lower().replace("х", "x").replace("×", "x").split("x")
        a, b = int(a), int(b)
        if a <= 0 or b <= 0:
            raise ValueError
        return a, b
    except ValueError:
        raise argparse.ArgumentTypeError(f"{what}: нужно два числа через x, например 42x28")


def collect(paths, recursive, out_root):
    """Возвращает список (файл, корень) — корень нужен, чтобы повторить подпапки в папке вывода."""
    found = []
    skip = os.path.abspath(out_root) if out_root else None
    for p in paths:
        if os.path.isfile(p):
            if p.lower().endswith(EXT):
                found.append((p, os.path.dirname(p) or "."))
            else:
                print(f"пропущено (не картинка): {p}")
        elif os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d.lower() != "webp" and os.path.abspath(os.path.join(root, d)) != skip]
                for name in sorted(files):
                    if name.lower().endswith(EXT):
                        found.append((os.path.join(root, name), p))
                if not recursive:
                    break
        else:
            print(f"не найдено: {p}")
    return found


def target_size(w, h, args):
    if args.cells:
        return args.cells[0] * args.px, args.cells[1] * args.px
    if args.size:
        return args.size
    if args.max and max(w, h) > args.max:
        k = args.max / max(w, h)
        return max(1, round(w * k)), max(1, round(h * k))
    return w, h


def mb(n):
    return f"{n / 1048576:.1f} МБ" if n >= 1048576 else f"{max(1, n // 1024)} КБ"


def main():
    for stream in (sys.stdout, sys.stderr):  # русский текст в консоли Windows
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Переводит картинки в WebP. Исходники не трогает.",
                                 epilog="Примеры: см. начало файла или README.md")
    ap.add_argument("paths", nargs="+", help="файлы или папки с картинками")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--max", type=int, metavar="N", help="ужать до N px по длинной стороне (меньшие не увеличиваются)")
    g.add_argument("--size", type=lambda s: parse_pair(s, "--size"), metavar="ШxВ", help="точный размер в пикселях, например 2940x1960")
    g.add_argument("--cells", type=lambda s: parse_pair(s, "--cells"), metavar="КxР", help="карта под сетку: клеток по ширине x по высоте")
    ap.add_argument("--px", type=int, default=70, help="пикселей на клетку для --cells (по умолчанию 70, как в Roll20)")
    ap.add_argument("-q", "--quality", type=int, default=90, help="качество 1–100 (по умолчанию 90)")
    ap.add_argument("--lossless", action="store_true", help="без потерь (файл больше; для пиксель-арта и чертежей)")
    ap.add_argument("-o", "--out", metavar="ПАПКА", help="куда класть (по умолчанию — подпапка webp рядом с исходниками)")
    ap.add_argument("-r", "--recursive", action="store_true", help="заходить в подпапки")
    ap.add_argument("--overwrite", action="store_true", help="перезаписывать готовые .webp (по умолчанию пропускаются)")
    args = ap.parse_args()
    if not 1 <= args.quality <= 100:
        ap.error("--quality: число от 1 до 100")

    files = collect(args.paths, args.recursive, args.out)
    if not files:
        sys.exit("Картинок не найдено (ищу: " + ", ".join(EXT) + ").")

    done = skipped = failed = 0
    total_in = total_out = 0
    for src, root in files:
        rel = os.path.relpath(src, root)
        out_dir = os.path.join(args.out, os.path.dirname(rel)) if args.out else os.path.join(os.path.dirname(src) or ".", "webp")
        dst = os.path.join(out_dir, os.path.splitext(os.path.basename(src))[0] + ".webp")
        if os.path.exists(dst) and not args.overwrite:
            skipped += 1
            print(f"уже есть, пропущено: {dst}")
            continue
        try:
            im = ImageOps.exif_transpose(Image.open(src))
            im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info) else "RGB")
            w0, h0 = im.size
            w, h = target_size(w0, h0, args)
            note = ""
            if (w, h) != (w0, h0):
                if (args.cells or args.size) and abs(w / h - w0 / h0) > 0.02 * (w0 / h0):
                    note = "  ! пропорции другие — картинка растянута"
                im = im.resize((w, h), Image.LANCZOS)
            os.makedirs(out_dir, exist_ok=True)
            if args.lossless:
                im.save(dst, "WEBP", lossless=True, method=6)
            else:
                im.save(dst, "WEBP", quality=args.quality, method=6)
            a, b = os.path.getsize(src), os.path.getsize(dst)
            total_in += a
            total_out += b
            done += 1
            print(f"{os.path.basename(src)}: {a // 1024} КБ -> {b // 1024} КБ, {w}x{h}{note}")
        except Exception as e:  # битый файл не должен останавливать всю папку
            failed += 1
            print(f"ОШИБКА {src}: {e}")

    line = f"Готово: {done}"
    if skipped:
        line += f", пропущено {skipped}"
    if failed:
        line += f", с ошибкой {failed}"
    if done:
        line += f". Было {mb(total_in)}, стало {mb(total_out)}"
    print(line)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
