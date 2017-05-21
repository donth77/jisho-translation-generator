from lxml import html
import sys, os, requests, urllib, json, datetime, xlsxwriter

def print_log(msg, file_only):
    now = datetime.datetime.now()
    print(now, " - ", msg, file=log_file)
    if not file_only:
        print(now, " - ", msg, flush=True)

def print_error(e, msg):
    now = datetime.datetime.now()
    print(now, " - ERROR - " + type(e).__name__ + "\n", e, file=log_file)
    print(now, " - ERROR - ", msg, file=log_file)
    print(now, " - ERROR - " + type(e).__name__ + "\n", e, flush=True)
    print(now, " - ERROR - " , msg, flush=True)

def progress(msg, iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    os.system('cls')
    print(msg)
    print("\r%s |%s| %s%% %s \n" % (prefix, bar, percent, suffix), end = '\r', flush=True)
    if iteration == total: 
        print()
        
def find_translation(word):
    response = requests.get(url)
    json_data = json.loads(response.text)
    print_log("Finding translation for " + word, True)
    if json_data["data"]:
        data = json_data["data"][0]
        japanese = data["japanese"][0]
        if "word" in japanese and not japanese["word"] == word or not "word" in japanese:
            print_log("Exact match not found.", True)
        if "reading" in japanese:
            reading = japanese["reading"]
        else:
            reading = ""
            print_log("Reading not found.", True)
        english_definitions = data["senses"][0]["english_definitions"]
        total_len = 0
        i = 0
        translation_result = ""
        for defn in english_definitions:
            if total_len >= translation_char_limit:
                 translation_result += "".join(["\n(",str(i + 1),") ",defn, "; "])
            else:
                 translation_result += "".join(["(",str(i + 1),") ",defn, "; "])
            total_len += len(defn)
            i += 1
        translation_result = translation_result.rstrip("; ")
        print_log(word + "(" + reading + ")", True)
        print_log(translation_result + "\n", True)
        worksheet.write("A" + str(iteration), word)
        worksheet.write("B" + str(iteration), reading)
        worksheet.write("C" + str(iteration), translation_result)            

input_filestr = "input.txt"
file_name = "translation-generator"
now_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
log_dir = "logs/"
output_dir = "output/"
log_filestr = file_name + "_" + now_str + ".log"

prog_prefix = "Progress:"
prog_suffix = "Complete"

nonblank_lines = []

input_file = open(input_filestr, encoding="utf-8")
for l in input_file:
    line = l.rstrip()
    if line:
        nonblank_lines.append(line)
line_count = len(nonblank_lines)
if line_count == 0:
    print_log("Input file is empty. Terminating...", False)
    sys.exit()
    
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

completion_val = 100
translation_char_limit = 75
prog_length = int(completion_val / 2)
iteration_step = int(line_count / completion_val)
iteration = 1
retry_url = False
max_retries = 5
workbook = xlsxwriter.Workbook(output_dir + file_name + "_" + now_str + ".xlsx")
worksheet = workbook.add_worksheet()
message = "Generating translations..."

progress(message, iteration - 1, line_count, prefix = prog_prefix, suffix = prog_suffix, length = prog_length)
try:
    with open(log_dir + log_filestr, "w", encoding="utf-8") as log_file:
        while (iteration < line_count):
            for line in nonblank_lines:
                url = "http://jisho.org/api/v1/search/words?keyword="+ urllib.parse.quote(line)
                try:
                    find_translation(line)
                except Exception as e:
                    retry_url = True
                    print_error(e, "Retrying...")

                num_retries = 0
                while retry_url and num_retries < max_retries:
                    num_retries = num_retries + 1
                    try:
                        find_translation(line)
                        retry_url = False
                    except Exception as e:
                        print_error(e, "Retrying...")
                if num_retries == max_retries:
                    print_log("Max retries reached. Skipping...", False)


                if iteration % iteration_step == 0:
                    progress(message, iteration, line_count, prefix = prog_prefix, suffix = prog_suffix, length = prog_length)
                iteration = iteration + 1
        progress(message, iteration - 1, line_count, prefix = prog_prefix, suffix = prog_suffix, length = prog_length)
        print_log("Completed!", False)
    input_file.close()
    log_file.close()
    workbook.close()
except Exception as e:
    print_error(e, "Terminating...")
    sys.exit()
    


