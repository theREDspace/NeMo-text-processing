def int_to_roman(num):
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
        ]
    syb = [
        "M", "CM", "D", "CD",
        "C", "XC", "L", "XL",
        "X", "IX", "V", "IV",
        "I"
        ]
    roman_num = ''
    i = 0
    while  num > 0:
        for _ in range(num // val[i]):
            roman_num += syb[i]
            num -= val[i]
        i += 1
    return roman_num

def num_to_french_final(n):
    units = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf"]
    teens = ["dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"]
    tens = ["", "dix", "vingt", "trente", "quarante", "cinquante", "soixante", "soixante-dix", "quatre-vingt"]

    if n < 10:
        return units[n]
    elif n < 20:
        return teens[n-10]
    elif n < 70:
        if n % 10 == 1:
            return tens[n // 10] + " et un"
        elif n % 10 == 0:
            return tens[n // 10]
        else:
            return tens[n // 10] + "-" + units[n % 10]
    elif n < 80:
        if n % 10 == 1:
            return "soixante et onze"
        elif n % 10 == 0:
            return tens[6] + "-" + teens[n - 70]
        else:
            return "soixante-" + teens[(n - 60) % 10]
    elif n < 90:
        return tens[8] + "-" + units[n % 10]
    elif n < 100:
        return tens[8] + "-" + teens[n % 10]
    elif n == 100:
        return "cent"
    elif n < 200:
        return "cent-" + num_to_french_final(n % 100).replace(' ', '-')
    elif n < 1000:
        cent_suffix = "s" if n % 100 == 0 else "-" + num_to_french_final(n % 100).replace(' ', '-')
        return num_to_french_final(n // 100) + "-cent" + cent_suffix
    elif n == 1000:
        return "mille"
    elif n < 2001:
        mille_prefix = "mille" if n // 1000 == 1 else num_to_french_final(n // 1000).replace(' ', '-') + "-mille"
        mille_suffix = "s" if n % 1000 == 0 else "-" + num_to_french_final(n % 1000).replace(' ', '-')
        return mille_prefix + mille_suffix
    
# Generate a TSV of roman numerals from 1 to 2000 with the French prefix
tsv_content = ""
for i in range(1, 2001):
    roman_numeral = int_to_roman(i)
    french_prefix = num_to_french_final(i)
    tsv_content += f"{roman_numeral}\t{french_prefix}\n"

# Save the TSV content to a file
file_path = 'roman_to_spoken.tsv'
with open(file_path, 'w') as file:
    file.write(tsv_content)