def remove_duplicates(input_file, output_file):
    unique_lines = set()
    print('I am here')
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            if line not in unique_lines:
                outfile.write(line)
                unique_lines.add(line)

input_file = 'significant_drops.txt'  # Путь к исходному файлу
output_file = 'unique_significant_drops.txt'  # Путь к новому файлу без дубликатов

remove_duplicates(input_file, output_file)

