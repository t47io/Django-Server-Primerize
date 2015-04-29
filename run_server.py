import binascii
import cherrypy
import glob
import os
import subprocess
import sys
import time
import random 
# import re
# from scipy.stats import *
from const import *
from helper import *

class Root:

    def __init__(self):
        pass
    def handle_error():
        cherrypy.response.status = 500
        cherrypy.response.body = load_html(PATH_500)

    _cp_config = {
        'error_page.404': PATH_404,
        'request.error_response': handle_error,
        'request.show_tracebacks': False,
    }

    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("home")
    @cherrypy.expose
    def design(self):
        return load_html(PATH_DESIGN).replace("__SEQ__", "").replace("__MIN_TM__", str(DEF_MIN_TM)).replace("__NUM_PRIMERS__", "auto").replace("__MAX_LEN__", str(DEF_MAX_LEN)).replace("__MIN_LEN__", str(DEF_MIN_LEN)).replace("__TAG__", "").replace("__LEN__", "0").replace("__IS_NUM_PRMS__", "").replace("__IS_NUM_PRMS_DIS__", "disabled=\"disabled\"").replace("__IS_T7__", "checked").replace("__RESULT__", "")
    @cherrypy.expose
    def home(self):
        return load_html(PATH_HOME)
    @cherrypy.expose
    def tutorial(self):
        return load_html(PATH_TUTORIAL)
    @cherrypy.expose
    def license(self):
        return load_html(PATH_LICENSE)
    @cherrypy.expose
    def download(self):
        return load_html(PATH_DOWNLOAD).replace("__SCRIPT__", "<script src=\"/res/js/download.js\"></script>")
    @cherrypy.expose
    def about(self):
        return load_html(PATH_ABOUT)

    @cherrypy.expose
    def result(self, job_id):
        if not job_id: raise cherrypy.HTTPRedirect("home")
        file_name = "cache/result_%s.html" % job_id
        if os.path.exists(file_name):
            return load_html(file_name)
        else:
            return load_html(PATH_404)

    @cherrypy.expose
    def design_primers(self, sequence, tag, min_Tm, num_primers, max_length, min_length, is_num_primers, is_t7, job_id):

        seq = sequence.upper().replace("U", "T")
        sequence = ""
        for char in seq:
            if ord(char) not in (10, 13, 32):
                sequence += char
        if len(sequence) < 60 or not is_valid_sequence(sequence):
            if not sequence:
                return rest.design(self)

            msg = "<br/><hr/><div class=\"container theme-showcase\"><h2>Output Result:</h2><div class=\"alert alert-danger\"><p><b>ERROR</b>: Invalid sequence input.</p></div>"
            return get_first_part_of_page(sequence, tag, min_Tm, num_primers, max_length, min_length, is_num_primers, is_t7).replace("__RESULT__", msg)


        try:
            min_Tm = float(min_Tm)
            if ("1" not in is_num_primers) or not num_primers or num_primers in (str(DEF_NUM_PRM), "auto"):
                num_primers = DEF_NUM_PRM
            else:
                num_primers = int(num_primers[0])
            max_length = int(max_length)
            min_length = int(min_length)
        except ValueError:
            if not (type(num_primers) is int): num_primers = num_primers[0]
            msg = "<br/><hr/><div class=\"container theme-showcase\"><h2>Output Result:</h2><div class=\"alert alert-danger\"><p><b>ERROR</b>: Invalid advanced options input.</p></div>"
            return get_first_part_of_page(sequence, tag, min_Tm, num_primers, max_length, min_length, is_num_primers, is_t7).replace("__RESULT__", msg)
        if num_primers != DEF_NUM_PRM and num_primers % 2 != 0:
            msg = "<br/><hr/><div class=\"container theme-showcase\"><h2>Output Result:</h2><div class=\"alert alert-danger\"><p><b>ERROR</b>: Invalid advanced options input: <b>#</b> number of primers must be <b><u>EVEN</u></b>.</p></div>"
            return get_first_part_of_page(sequence, tag, min_Tm, num_primers, max_length, min_length, is_num_primers, is_t7).replace("__RESULT__", msg)
        if "1" in is_t7: (sequence, flag) = is_t7_present(sequence)
        if not tag: tag = "primer"


        t0 = time.time()
        f_run = subprocess.check_output(["matlab", "-nojvm", "-nodisplay", "-nosplash", "-r", "design_primers(\'%s\',%d,%d,[],%d,%d,[],1); exit()" % (sequence, min_Tm, num_primers, max_length, min_length)], shell=False)
        # f_run = subprocess.check_output(["octave", "--eval", "design_primers(\'%s\',%d,%d,[],%d,%d,[],1); exit()" % (sequence, min_Tm, num_primers, max_length, min_length)], shell=False)
        lines = f_run.split("\n")
        t_total = time.time() - t0

        lines = [line.replace("\n","") for line in lines]
        if lines[-2] and lines[-2][0] == "?":
            msg = "<br/><hr/><div class=\"container theme-showcase\"><h2>Output Result:</h2><div class=\"alert alert-danger\"><p><b>ERROR</b>: No solution found, please adjust advanced options.</p></div>"
            return get_first_part_of_page(sequence, tag, min_Tm, num_primers, max_length, min_length, is_num_primers, is_t7).replace("__RESULT__", msg)

        sec_break = [i for i in range(len(lines)) if lines[i] == "#"]
        self.lines_warning = lines[sec_break[0] : sec_break[1]]
        self.lines_primers = lines[sec_break[1] + 2 : sec_break[2]]
        self.lines_assembly = lines[sec_break[2] + 1 : -1]

        script = ""
        if self.lines_warning != ['#']:
            script += "<br/><hr/><div class=\"container theme-showcase\"><div class=\"row\"><div class=\"col-md-8\"><h2>Output Result:</h2></div><div class=\"col-md-4\"><h4 class=\"text-right\"><span class=\"label label-violet\">JOB_ID</span>: <span class=\"label label-inverse\">__JOB_ID___</span></h4><a href=\"__FILE_NAME__\" class=\"btn btn-blue pull-right\" style=\"color: #ffffff;\" title=\"Output in plain text\" download>&nbsp;Save Result&nbsp;</a></div></div><br/><div class=\"alert alert-warning\" title=\"Mispriming alerts\"><p>"
            for line in self.lines_warning:
                if line[0] == "@":
                    script += "<b>WARNING</b>"
                    for char in line[8:]:
                        if char == "F":
                            script += "</b><span class=\"label label-info\">"
                        elif char == "R":
                            script += "</b><span class=\"label label-danger\">" 
                        elif char == "{":
                            script += "<font style=\"text-transform: uppercase;\"><b>"
                        elif char == "}":
                            script += "</span></font>"
                        elif char == "[":
                            script += "<span class=\"label label-success\">"
                        elif char == "]":
                            script += "</span>"
                        elif char == "(":
                            script += "<span class=\"label label-default\">"
                        elif char == ")":
                            script += "</span>"
                        else:
                            script += char 
                    script += "<br/>"
        else:
            script += "<div class=\"container theme-showcase\"><div class=\"row\"><div class=\"col-md-8\"><h2>Output Result:</h2></div><div class=\"col-md-4\"><h4 class=\"text-right\"><span class=\"label label-violet\">JOB_ID</span>: <span class=\"label label-inverse\">__JOB_ID___</span></h4><a href=\"__FILE_NAME__\" class=\"btn btn-blue pull-right\" title=\"Output in plain text\" download>&nbsp;Download&nbsp;</a></div></div><br/><div class=\"alert alert-success\" title=\"No alerts\"><p>"
            script += "<b>SUCCESS</b>: No potential mis-priming found. See results below.<br/>"

        script +=  "__NOTE_T7__</p></div><div class=\"row\"><div class=\"col-md-12\"><div class=\"alert alert-orange\"> <b>Time elapsed</b>: %.1f" % t_total + " s.</div></div></div>"

        script += "<div class=\"row\"><div class=\"col-md-12\"><div class=\"panel panel-primary\"><div class=\"panel-heading\"><h2 class=\"panel-title\">Designed Primers</h2></div><div class=\"panel-body\"><table class=\"table table-hover\" ><thead><tr><th class=\"col-md-1\">#</th><th class=\"col-md-1\">Length</th><th class=\"col-md-10\">Sequence</th></tr></thead><tbody>"
        for line in self.lines_primers:
            line = line.split("\t")
            num = "<b>" + line[0][7:]
            if int(line[0][7:]) % 2 == 0:
                num = "<tr><td>" + num + "<span class=\"label label-danger\">R</span></b>"
            else:
                num = "<tr class=\"warning\"><td>" + num + "<span class=\"label label-info\">F</span></b>"
            script += num + "</td><td><em>" + line[1] + "</em></td><td style=\"word-break: break-all;\">" + line[2] + "</td></tr>"

        script += "</tbody></table></div></div></div></div><div class=\"row\"><div class=\"col-md-12\"><div class=\"panel panel-green\"><div class=\"panel-heading\"><h2 class=\"panel-title\">Assembly Scheme</h2></div><div class=\"panel-body\"><pre>"
        for line in self.lines_assembly:
            if line:
                if line[0] == "~":
                    script += "<span class=\"label-white label-primary\">" + line[1:] + "</span><br/>"
                elif line[0] == "=":
                    script += "<span class=\"label-warning\">" + line[1:] + "</span><br/>"
                elif line[0] == "^":
                    for char in line[1:]:
                        if char in ("A","T","C","G"):
                            script += "<span class=\"label-info\">" + char + "</span>"
                        else:
                            script += char
                    script += "<br/>"
                elif line[0] == "!":
                    for char in line[1:]:
                        if char in ("A","T","C","G"):
                            script += "<span class=\"label-white label-danger\">" + char + "</span>"
                        else:
                            script += char
                    script += "<br/>"
                else:
                    for char in line[1:]:
                        if char == "{":
                            script += "<kbd>"
                        elif char == "}":
                            script += "</kbd>" 
                        else:
                            script += char 
                    script += "<br/>"
            else:
                script += "<br/>"

        script += "</pre></div></div></div></div></p></div>"


        # f = tempfile.NamedTemporaryFile(mode="w+b", prefix="result_", suffix=".txt", dir="cache", delete=False)
        # job_id = binascii.b2a_hex(os.urandom(7)) #f.name[-17:]
        file_name = "cache/result_%s.txt" % job_id
        f = open(file_name, "w")

        f.write("Primerize Result\n\nINPUT\n=====\n%s\n" % sequence)
        f.write("#\nMIN_TM: %.1f\n" % min_Tm)
        if num_primers == DEF_NUM_PRM:
            f.write("NUM_PRIMERS: auto (unspecified)")
        else:
            f.write("NUM_PRIMERS: %d" % num_primers)
        f.write("\nMAX_LENGTH: %d\nMIN_LENGTH: %d\n" % (max_length, min_length))
        if "1" in is_t7:
            str_t7 = "CHECK_T7: feature enabled, "
            if flag:
                str_t7 = str_t7 + "T7 promoter sequence present.\n"
            else:
                str_t7 = str_t7 + "T7 promoter sequence missing, automatically prepended.\n"
        else:
            str_t7 = "CHECK_T7: feature disabled.\n"
        f.write(str_t7)
        script = script.replace("__NOTE_T7__", str_t7.replace("\n","").replace("CHECK_T7","<b>CHECK_T7</b>"))

        f.write("\n\nOUTPUT\n======\n")
        for line in self.lines_warning:
            if line[0] == "@":
                f.write("%s\n" % line[1:].replace("{","").replace("}","").replace("(","").replace(")","").replace("[","").replace("]","").replace("Ff","").replace("Rr",""))
        f.write("#\n")
        for line in self.lines_primers:
            f.write("%s\n" % line)
        f.write("#\n")
        for line in self.lines_assembly:
            if line and line[0] in ("$","!","^","=","~"):
                f.write("%s\n" % line[1:].replace("{","").replace("}",""))
        f.write("#\n\n------/* IDT USER: for primer ordering, copy and paste to Bulk Input */------\n------/* START */------\n")
        for line in self.lines_primers:
            line = line.split("\t")
            f.write("%s\t%s\t25nm\tSTD\n" % (line[0].replace("primer", tag), line[2]))
        f.write("------/* END */------\n------/* NOTE: use \"Lab Ready\" for \"Normalization\" */------\n")

        script = script.replace("__FILE_NAME__", "/"+file_name).replace("__JOB_ID___", job_id)
        f.close()

        f = open("cache/result_%s.html" % job_id, "w")
        html_content = get_first_part_of_page(sequence, tag, min_Tm, num_primers, max_length, min_length, is_num_primers, is_t7).replace("__RESULT__", script)
        f.write(html_content)
        f.close()
        raise cherrypy.HTTPRedirect("result/%s" % job_id)
        # return html_content


    @cherrypy.expose
    def cleanup_old(self):
        older_7days = time.time() - JOB_KEEP_EXPIRE * 86400

        for f in glob.glob("cache/*"):
            if (os.stat(f).st_mtime < older_7days):
                os.remove(f)


    @cherrypy.expose
    def demo_P4P6(self):
        self.cleanup_old()
        return self.design_primers(seq_P4P6, "P4P6_2HP", str(DEF_MIN_TM), str(DEF_NUM_PRM), str(DEF_MAX_LEN), str(DEF_MIN_LEN), "0", "1", binascii.b2a_hex(os.urandom(7)))    
    @cherrypy.expose
    def test_random(self):
        seq = seq_T7 + ''.join(random.choice('CGTA') for _ in xrange(500))
        return self.design_primers(seq, "scRNA", str(DEF_MIN_TM), str(DEF_NUM_PRM), str(DEF_MAX_LEN), str(DEF_MIN_LEN), "0", "1", binascii.b2a_hex(os.urandom(7)))  

    @cherrypy.expose
    def submit_download(self, first_name, last_name, email, inst, dept, is_subscribe):

        is_valid = is_valid_name(first_name, "- ", 2) and is_valid_name(last_name, "- ", 1) and is_valid_name(inst, "()-, ", 4) and is_valid_name(dept, "()-, ", 4) and is_valid_email(email)

        if is_valid:
            f = open("src/usr_tab.csv", "a")
            f.write("%s," % time.strftime("%c"))
            if "1" in is_subscribe:
                f.write("1")
            else:
                f.write("0")
            f.write(",%s,%s,%s,%s,%s\n" % (first_name, last_name, email, inst, dept))
            f.close()
            return load_html(PATH_DOWNLOAD).replace("__SCRIPT__", "<script src=\"/res/js/download_link.js\"></script>")

        else:
            script = load_html(PATH_DOWNLOAD)
            script = script.replace("__F_NAME__", first_name).replace("__L_NAME__", last_name).replace("__EMAIL__", email).replace("__INST__", inst).replace("__DEPT__", dept)
            if "1" in is_subscribe: 
                script = script.replace("__IS_SUBSCRIBE__", "checked=\"yes\"") 
            else:
                script = script.replace("__IS_SUBSCRIBE__", "") 
            return script.replace("__SCRIPT__", "<script src=\"/res/js/download_error.js\"></script>")

    # @cherrypy.expose
    # def test(self):
    #     raise ValueError
    @cherrypy.expose
    def error(self):
        raise ValueError



if __name__ == "__main__":
    server_state = "dev"
    if len(sys.argv) > 1:
        server_state = sys.argv[1]
    if server_state not in ("dev","release"):
        print "Usage:\n\tpython run_server.py [flag]\n\n\tflag\t[required]\tuse \"release\" for hosting server\n\t\t\t\tuse \"dev\" for development test\n"
        raise SystemError("ERROR: Only can do development or release")
    if server_state == "release":
        socket_host = "171.65.23.206"
    else:
        socket_host = "127.0.0.1"

    cherrypy.config.update( {
        "server.socket_host":socket_host, 
        "server.socket_port":8080,
        "tools.staticdir.root": os.path.abspath(os.path.join(os.path.dirname(__file__), "")),
        #"tools.statiddir.root": "/Users/skullnite/Downloads"
    } )
    #print os.path.abspath(os.path.join(__file__, "static"))
    #cherrypy.quickstart( rest(), "/", "development.conf" )
    
    cherrypy.quickstart(Root(), "", config=QUICKSTART_CONFIG)

