<<<<<<< HEAD
<<<<<<< HEAD
## Задача 1

```bash
cut -d: -f1 /etc/passwd | sort
```

## Задача 2

```bash
grep -Ev '^#|^$' /etc/protocols | awk '{print $2, $1}' | sort -rn | head -5
```

## Задача 3

```bash
nano banner
```

```bash
set -euo pipefail
text="$1"
len=${#text}
border_len=$((len + 2))
border=$(printf '%*s' "$border_len" '' | tr ' ' '-')
printf '+%s+\n' "$border"
printf '| %s |\n' "$text"
printf '+%s+\n' "$border"
```

```bash
chmod +x banner
./banner "Hello from RTU MIREA!"
```

## Задача 4

```bash
grep -oE '[A-Za-z_][A-Za-z0-9_]*' hello.c | sort -u | tr '\n' ' '
```

## Задача 5

```bash
#!/usr/bin/env bash

if [ "$#" -ne 1 ]; then
    echo "Использование: $0 <файл>" >&2
    exit 1
fi

src=$1
dest_dir=/usr/local/bin

if [ ! -f "$src" ]; then
    echo "Ошибка: файл '$src' не найден" >&2
    exit 1
fi

chmod 755 "$src"
cp "$src" "$dest_dir/$(basename "$src")"
echo "Команда $(basename "$src") зарегистрирована в $dest_dir"
```

```bash
chmod +x reg
sudo ./reg banner
banner "Hello from RTU MIREA!"
```

## Задача 6

```bash
#!/usr/bin/env bash

dir=${1:-.}

if [ ! -d "$dir" ]; then
    echo "Ошибка: '$dir' не каталог" >&2
    exit 1
fi

while IFS= read -r -d '' file; do
    first=$(head -n 1 "$file")
    case "${file##*.}" in
        c|js) pattern='^[[:space:]]*(//|/\*)' ;;
        py)   pattern='^[[:space:]]*#' ;;
    esac
    if [[ $first =~ $pattern ]]; then
        echo "есть комментарий: $file"
    else
        echo "нет комментария:  $file"
    fi
done < <(find "$dir" -type f \( -name '*.c' -o -name '*.js' -o -name '*.py' \) -print0)
```

```bash
chmod +x check_comment
./check_comment ~/project
```

## Задача 7

```bash
#!/usr/bin/env bash

dir=${1:-.}

if [ ! -d "$dir" ]; then
    echo "Ошибка: '$dir' не каталог" >&2
    exit 1
fi

find "$dir" -type f -size +0 -exec sha256sum {} + \
    | sort \
    | uniq -w64 --all-repeated=separate \
    | cut -c67-
```

```bash
chmod +x finddup
./finddup ~/project
```

## Задача 8

```bash
#!/usr/bin/env bash

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "Использование: $0 <расширение> [каталог]" >&2
    exit 1
fi

ext=${1#.}
dir=${2:-.}

if [ ! -d "$dir" ]; then
    echo "Ошибка: '$dir' не каталог" >&2
    exit 1
fi

archive="archive_$ext.tar"

find "$dir" -maxdepth 1 -type f -name "*.$ext" -print0 \
    | tar --null -cvf "$archive" -T -

echo "Создан архив: $archive"
```

```bash
chmod +x archive_ext
./archive_ext c ~/testdir
```

## Задача 9

```bash
#!/usr/bin/env bash

if [ "$#" -ne 2 ]; then
    echo "Использование: $0 <входной_файл> <выходной_файл>" >&2
    exit 1
fi

in=$1
out=$2

if [ ! -f "$in" ]; then
    echo "Ошибка: файл '$in' не найден" >&2
    exit 1
fi

if [ "$in" -ef "$out" ]; then
    echo "Ошибка: входной и выходной файлы должны быть разными" >&2
    exit 1
fi

sed 's/    /\t/g' "$in" > "$out"
```

```bash
printf 'a    b\n        c\nd  e\n' > in.txt
chmod +x tabify
./tabify in.txt out.txt
cat -A out.txt
```

## Задача 10

```bash
#!/usr/bin/env bash

if [ "$#" -ne 1 ]; then
    echo "Использование: $0 <каталог>" >&2
    exit 1
fi

dir=$1

if [ ! -d "$dir" ]; then
    echo "Ошибка: '$dir' не каталог" >&2
    exit 1
fi

find "$dir" -maxdepth 1 -type f -empty -name '*.txt'
```

```bash
mkdir -p ~/testdir2
cd ~/testdir2
touch empty1.txt empty2.txt
echo 'text' > full.txt
touch empty3.log
cd ~
chmod +x emptytxt
./emptytxt ~/testdir2
```
=======
## Задача 1

```bash
cut -d: -f1 /etc/passwd | sort
```

## Задача 2

```bash
grep -Ev '^#|^$' /etc/protocols | awk '{print $2, $1}' | sort -rn | head -5
```

## Задача 3

```bash
nano banner
```

```bash
set -euo pipefail
text="$1"
len=${#text}
border_len=$((len + 2))
border=$(printf '%*s' "$border_len" '' | tr ' ' '-')
printf '+%s+\n' "$border"
printf '| %s |\n' "$text"
printf '+%s+\n' "$border"
```

```bash
chmod +x banner
./banner "Hello from RTU MIREA!"
```

## Задача 4

```bash
grep -oE '[A-Za-z_][A-Za-z0-9_]*' hello.c | sort -u | tr '\n' ' '
```

## Задача 5

```bash
#!/usr/bin/env bash

if [ "$#" -ne 1 ]; then
    echo "Использование: $0 <файл>" >&2
    exit 1
fi

src=$1
dest_dir=/usr/local/bin

if [ ! -f "$src" ]; then
    echo "Ошибка: файл '$src' не найден" >&2
    exit 1
fi

chmod 755 "$src"
cp "$src" "$dest_dir/$(basename "$src")"
echo "Команда $(basename "$src") зарегистрирована в $dest_dir"
```

```bash
chmod +x reg
sudo ./reg banner
banner "Hello from RTU MIREA!"
```

## Задача 6

```bash
#!/usr/bin/env bash

dir=${1:-.}

if [ ! -d "$dir" ]; then
    echo "Ошибка: '$dir' не каталог" >&2
    exit 1
fi

while IFS= read -r -d '' file; do
    first=$(head -n 1 "$file")
    case "${file##*.}" in
        c|js) pattern='^[[:space:]]*(//|/\*)' ;;
        py)   pattern='^[[:space:]]*#' ;;
    esac
    if [[ $first =~ $pattern ]]; then
        echo "есть комментарий: $file"
    else
        echo "нет комментария:  $file"
    fi
done < <(find "$dir" -type f \( -name '*.c' -o -name '*.js' -o -name '*.py' \) -print0)
```

```bash
chmod +x check_comment
./check_comment ~/project
```

## Задача 7

```bash
#!/usr/bin/env bash

dir=${1:-.}

if [ ! -d "$dir" ]; then
    echo "Ошибка: '$dir' не каталог" >&2
    exit 1
fi

find "$dir" -type f -size +0 -exec sha256sum {} + \
    | sort \
    | uniq -w64 --all-repeated=separate \
    | cut -c67-
```

```bash
chmod +x finddup
./finddup ~/project
```

## Задача 8

```bash
#!/usr/bin/env bash

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "Использование: $0 <расширение> [каталог]" >&2
    exit 1
fi

ext=${1#.}
dir=${2:-.}

if [ ! -d "$dir" ]; then
    echo "Ошибка: '$dir' не каталог" >&2
    exit 1
fi

archive="archive_$ext.tar"

find "$dir" -maxdepth 1 -type f -name "*.$ext" -print0 \
    | tar --null -cvf "$archive" -T -

echo "Создан архив: $archive"
```

```bash
chmod +x archive_ext
./archive_ext c ~/testdir
```

## Задача 9

```bash
#!/usr/bin/env bash

if [ "$#" -ne 2 ]; then
    echo "Использование: $0 <входной_файл> <выходной_файл>" >&2
    exit 1
fi

in=$1
out=$2

if [ ! -f "$in" ]; then
    echo "Ошибка: файл '$in' не найден" >&2
    exit 1
fi

if [ "$in" -ef "$out" ]; then
    echo "Ошибка: входной и выходной файлы должны быть разными" >&2
    exit 1
fi

sed 's/    /\t/g' "$in" > "$out"
```

```bash
printf 'a    b\n        c\nd  e\n' > in.txt
chmod +x tabify
./tabify in.txt out.txt
cat -A out.txt
```

## Задача 10

```bash
#!/usr/bin/env bash

if [ "$#" -ne 1 ]; then
    echo "Использование: $0 <каталог>" >&2
    exit 1
fi

dir=$1

if [ ! -d "$dir" ]; then
    echo "Ошибка: '$dir' не каталог" >&2
    exit 1
fi

find "$dir" -maxdepth 1 -type f -empty -name '*.txt'
```

```bash
mkdir -p ~/testdir2
cd ~/testdir2
touch empty1.txt empty2.txt
echo 'text' > full.txt
touch empty3.log
cd ~
chmod +x emptytxt
./emptytxt ~/testdir2
```
>>>>>>> 5ee0153a07c119a480da98d883242a8595fc2d6e
=======
## Задача 1

```bash
cut -d: -f1 /etc/passwd | sort
```

## Задача 2

```bash
grep -Ev '^#|^$' /etc/protocols | awk '{print $2, $1}' | sort -rn | head -5
```

## Задача 3

```bash
nano banner
```

```bash
set -euo pipefail
text="$1"
len=${#text}
border_len=$((len + 2))
border=$(printf '%*s' "$border_len" '' | tr ' ' '-')
printf '+%s+\n' "$border"
printf '| %s |\n' "$text"
printf '+%s+\n' "$border"
```

```bash
chmod +x banner
./banner "Hello from RTU MIREA!"
```

## Задача 4

```bash
grep -oE '[A-Za-z_][A-Za-z0-9_]*' hello.c | sort -u | tr '\n' ' '
```

## Задача 5

```bash
#!/usr/bin/env bash

if [ "$#" -ne 1 ]; then
    echo "Использование: $0 <файл>" >&2
    exit 1
fi

src=$1
dest_dir=/usr/local/bin

if [ ! -f "$src" ]; then
    echo "Ошибка: файл '$src' не найден" >&2
    exit 1
fi

chmod 755 "$src"
cp "$src" "$dest_dir/$(basename "$src")"
echo "Команда $(basename "$src") зарегистрирована в $dest_dir"
```

```bash
chmod +x reg
sudo ./reg banner
banner "Hello from RTU MIREA!"
```

## Задача 6

```bash
#!/usr/bin/env bash

dir=${1:-.}

if [ ! -d "$dir" ]; then
    echo "Ошибка: '$dir' не каталог" >&2
    exit 1
fi

while IFS= read -r -d '' file; do
    first=$(head -n 1 "$file")
    case "${file##*.}" in
        c|js) pattern='^[[:space:]]*(//|/\*)' ;;
        py)   pattern='^[[:space:]]*#' ;;
    esac
    if [[ $first =~ $pattern ]]; then
        echo "есть комментарий: $file"
    else
        echo "нет комментария:  $file"
    fi
done < <(find "$dir" -type f \( -name '*.c' -o -name '*.js' -o -name '*.py' \) -print0)
```

```bash
chmod +x check_comment
./check_comment ~/project
```

## Задача 7

```bash
#!/usr/bin/env bash

dir=${1:-.}

if [ ! -d "$dir" ]; then
    echo "Ошибка: '$dir' не каталог" >&2
    exit 1
fi

find "$dir" -type f -size +0 -exec sha256sum {} + \
    | sort \
    | uniq -w64 --all-repeated=separate \
    | cut -c67-
```

```bash
chmod +x finddup
./finddup ~/project
```

## Задача 8

```bash
#!/usr/bin/env bash

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "Использование: $0 <расширение> [каталог]" >&2
    exit 1
fi

ext=${1#.}
dir=${2:-.}

if [ ! -d "$dir" ]; then
    echo "Ошибка: '$dir' не каталог" >&2
    exit 1
fi

archive="archive_$ext.tar"

find "$dir" -maxdepth 1 -type f -name "*.$ext" -print0 \
    | tar --null -cvf "$archive" -T -

echo "Создан архив: $archive"
```

```bash
chmod +x archive_ext
./archive_ext c ~/testdir
```

## Задача 9

```bash
#!/usr/bin/env bash

if [ "$#" -ne 2 ]; then
    echo "Использование: $0 <входной_файл> <выходной_файл>" >&2
    exit 1
fi

in=$1
out=$2

if [ ! -f "$in" ]; then
    echo "Ошибка: файл '$in' не найден" >&2
    exit 1
fi

if [ "$in" -ef "$out" ]; then
    echo "Ошибка: входной и выходной файлы должны быть разными" >&2
    exit 1
fi

sed 's/    /\t/g' "$in" > "$out"
```

```bash
printf 'a    b\n        c\nd  e\n' > in.txt
chmod +x tabify
./tabify in.txt out.txt
cat -A out.txt
```

## Задача 10

```bash
#!/usr/bin/env bash

if [ "$#" -ne 1 ]; then
    echo "Использование: $0 <каталог>" >&2
    exit 1
fi

dir=$1

if [ ! -d "$dir" ]; then
    echo "Ошибка: '$dir' не каталог" >&2
    exit 1
fi

find "$dir" -maxdepth 1 -type f -empty -name '*.txt'
```

```bash
mkdir -p ~/testdir2
cd ~/testdir2
touch empty1.txt empty2.txt
echo 'text' > full.txt
touch empty3.log
cd ~
chmod +x emptytxt
./emptytxt ~/testdir2
```
>>>>>>> 5ee0153a07c119a480da98d883242a8595fc2d6e
