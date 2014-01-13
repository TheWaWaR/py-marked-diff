#!/usr/bin/env python2
#coding: utf-8

import sys
import re
import cgi
import difflib
import commands
from jinja2 import Template

from .models import MarkedDiff


def get_diff_output(filename1, filename2):
    cmd = u'diff -u {0:s} {1:s}'.format(filename1, filename2)
    diff_out = commands.getstatusoutput(cmd)
    # print cmd, '<|>' ,diff_out
    return diff_out

    
def fill_blank(delta_ln1, delta_ln2, lst1, lst2):
    if delta_ln1 > delta_ln2:
        for i in range(delta_ln1-delta_ln2): lst2.append(('#', -1, ''))
    elif delta_ln2 > delta_ln1:
        for i in range(delta_ln2-delta_ln1): lst1.append(('#', -1, ''))

        
def get_aligned_blocks(t_diff_lines):
    rexp = r'@@ -(\w+),(\w+) \+(\w+),(\w+) @@'
    header = None
    lst1 = []
    lst2 = []
    ln1 = ln2 = -1
    delta_ln1 = delta_ln2 = 0
    for line in t_diff_lines:
        code = line[0]
        content = cgi.escape(line[1:])
        if code == '@':
            if (len(lst1) + len(lst2)) > 0:
                yield header, lst1, lst2
                lst1 = []
                lst2 = []
            header = line       # update header
            t_nums = re.match(rexp, header).groups()
            ln1 = int(t_nums[0])
            ln2 = int(t_nums[2])
            
            fill_blank(delta_ln1, delta_ln2, lst1, lst2)
            delta_ln1 = delta_ln2 = 0
        elif code in ('-', '+', ' '):
            if code == '-':
                lst1.append((code, ln1, content))
                delta_ln1 += 1
                ln1 += 1
            elif code == '+':
                lst2.append((code, ln2, content))
                delta_ln2 += 1
                ln2 += 1
            elif code == ' ':
                fill_blank(delta_ln1, delta_ln2, lst1, lst2)
                delta_ln1 = delta_ln2 = 0
                
                lst1.append((code, ln1, content))
                lst2.append((code, ln2, content))
                ln1 += 1
                ln2 += 1
        elif code == '\\':      # Ignore: No newline at end of file
            pass                
        else:
            print 'Error code: [ %s ]' % code
            raise ValueError

    fill_blank(delta_ln1, delta_ln2, lst1, lst2)
    yield header, lst1, lst2

    
# ==============================================================================
#  Compare tow lines
# ==============================================================================
HTML_FMT = '<span class="%s">%s</span>'

def split_line_idxs(dl):
    diff_dict = {
        ' ' : None,
        '+' : 'add',
        '-' : 'cut',
        '^' : 'diff'
    }
    i = oi = 0
    oc = dl[0]
    slices = []
    for c in dl:
        if c != oc:
            # print '[%d, %d, %r, %r]' % (oi, i, oc, c)
            slices.append((diff_dict[oc], oi, i))
            oc = c
            oi = i
        i += 1
    return slices

    
def build_html_line(line, slices):
    #: CSS class in ['diff', 'cut', 'add']
    #: See `diff_dict` in function `split_line_idxs`
    parts = []
    for cls, start, end in slices:
        if cls is not None:
            parts.append(HTML_FMT % (cls, line[start:end]))
        else:
            parts.append(line[start:end])
            
    last_slice_end = slices[-1][-1]
    parts.append(line[last_slice_end: -1])
    return ''.join(parts)

    
def process_line_diff(line1, line2):
    text1, text2 = [line1], [line2]
    d = difflib.Differ()
    diffs = list(d.compare(text1, text2))
    diffs_len = len(diffs)
    
    if diffs_len == 2:
        return HTML_FMT % ('diff', line1), HTML_FMT % ('diff', line2)
    elif diffs_len == 3:
        if diffs[1].startswith('? '):
            d1 = diffs[1][2:]
            slices1 = split_line_idxs(d1)
            return build_html_line(line1, slices1), line2
        elif diffs[2].startswith('? '):
            d2 = diffs[2][2:]
            slices2 = split_line_idxs(d2)
            return line1, build_html_line(line2, slices2),
        else:
            print diffs_len, line1, line2
            print '\n'.join(diffs)
            raise ValueError
    elif diffs_len == 4:
        d1, d2 = diffs[1][2:], diffs[3][2:]
        slices1 = split_line_idxs(d1)
        slices2 = split_line_idxs(d2)
        return build_html_line(line1, slices1), build_html_line(line2, slices2)
    else:
        print diffs_len, line1, line2
        print '\n'.join(diffs)
        raise ValueError
        
#### [END] ####        

        
def get_type(code1, code2):
    #: Type     ==> [+, #,  !=, ==]
    #:  +       ==> 当前文件有内容, 对应的文件补充虚拟行
    #:  #       ==> 每一个 '+' 都对应一个 '#', 代表一个虚拟行, 实际文件中并不存在该行, 所以不应该显示行号
    #:  !=      ==> 两个文件内容不一致但是在比较时可以对齐的行
    #:  ==      ==> 两个文件内容完全一致的行(行号不一定一样)
    type1 = type2 = None
    if code1 == code2 == ' ':
        type1 = type2 = '=='
    elif code1 == '-' and code2 == '+' and code1 != code2:
        type1 = type2 = '!='
    elif code1 == '#' and code2 == '+':
        type1, type2 = '#', '+'
    elif code1 == '-' and code2 == '#':
        type1, type2 = '+', '#'
    else:
        print code1, code2
        raise ValueError
        
    return type1, type2
    
    
def process_block(lst1, lst2):
    # Format = u'%(ln)d:%(type)s:%(line)s'
    part1 = []
    part2 = []
    for i in range(len(lst1)):
        code1, ln1, content1 = lst1[i]
        code2, ln2, content2 = lst2[i]
        # print lst1[i]
        # print lst2[i]
        type1, type2 = get_type(code1, code2)
        if type1 == type2 == '!=' and content1 != content2:
            content1, content2 = process_line_diff(content1, content2)
            
        line1 = u'{0:<2s}:{1:d}:{2:s}'.format(type1, ln1, content1)
        line2 = u'{0:<2s}:{1:d}:{2:s}'.format(type2, ln2, content2)
        part1.append(line1)
        part2.append(line2)
        # print '{0:<80s} | {1:<80s}'.format(line1, line2)
        
    return part1, part2


def parse_diff_result(result):
    lines = []
    if result is None: return lines
    
    for line in result.split('\n'):
        if line[:1] == ',':
            lines.append(None)
        else:
            line_num_end_index = line.find(':', 3)
            lines.append((line[:2], # 1. Line diff type
                          line[3:line_num_end_index], # 2. Line number
                          line[line_num_end_index+1:])) # 3. Line content
    return lines


def render_html(divid, result):
    tempalte_string = '''<div id="{{ divid }}" class="diff-part">
{% for line in lines %}
    {% if line is none %}<div class="part-spliter">[ ...... ]</div>
    {% elif line[0] == '+ ' %}<div class="add-line"><span class="line-number">{{ line[1] }}:</span><span class="content">{{ line[2] | safe }}</span></div>
    {% elif line[0] == '# ' %}<div class="virtual-line">&nbsp;</div>
    {% elif line[0] == '!=' %}<div class="diff-line"><span class="line-number">{{ line[1] }}:</span><span class="content">{{ line[2] | safe }}</span></div>
    {% else %}<div class="equal-line"><span class="line-number">{{ line[1] }}:</span><span class="content">{{ line[2] | safe }}</span></div>
    {% endif %}
{% endfor %}</div>'''
    t = Template(tempalte_string)
    lines = parse_diff_result(result)
    return t.render(divid=divid, lines=lines)

    
def render_empty_html(divid, result):
    _html = u'''<div id="%s" class="diff-part"><div class="part-spliter">[ 两个文件完全相同 ]</div></div>'''
    return _html % divid
    

def process_files_diff(filename1, filename2):
    diff_out = get_diff_output(filename1, filename2)
    diff_lines = diff_out[1].split('\n')

    rets1, rets2 = [], []
    for header, lst1, lst2 in get_aligned_blocks(diff_lines[2:]):
        # print header
        # print '--------------------'
        part1, part2 = process_block(lst1, lst2)
        if (len(part1) + len(part2)) > 0:
            part1.append(',')
            rets1.extend(part1)
            
            part2.append(',')
            rets2.extend(part2)
    result1 = '\n'.join(rets1)
    result2 = '\n'.join(rets2)
    html_result1 = render_html('file1', result1) if header is not None else render_empty_html('file1', result1)
    html_result2 = render_html('file2', result2) if header is not None else render_empty_html('file2', result2)

    data = {
        'filename1': filename1,
        'filename2': filename2,
        'result1': result1,
        'result2': result2,
        'html_result1': html_result1,
        'html_result2': html_result2
    }

    record = MarkedDiff()
    record.save(data)
    
    return record
    
    
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print 'Arguments Error'
        sys.exit()
        
    file_name_1 = sys.argv[1]
    file_name_2= sys.argv[2]
    ret1, ret2 = process_files_diff(file_name_1, file_name_2)
    print '============================================================'
    print ret1
    print '------------------------------'
    print ret2
    print '============================================================'
