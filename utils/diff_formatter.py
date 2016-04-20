#!/usr/bin/env python2
#coding: utf-8

import sys
import re
import cgi
import difflib
import commands
import json
from jinja2 import Template


def get_diff_output(filepath1, filepath2):
    ''' 调用命令行的 diff 获得初步比较结果 '''
    
    cmd = u'diff -u {0:s} {1:s}'.format(filepath1, filepath2)
    diff_out = commands.getstatusoutput(cmd)
    # print cmd, '<|>' ,diff_out
    return diff_out[1]

    
def fill_blank(delta_ln1, delta_ln2, lst1, lst2):
    ''' 用空行对齐比较块 '''
    
    if delta_ln1 > delta_ln2:
        for i in range(delta_ln1-delta_ln2): lst2.append(('#', -1, ''))
    elif delta_ln2 > delta_ln1:
        for i in range(delta_ln2-delta_ln1): lst1.append(('#', -1, ''))

        
def get_aligned_blocks(t_diff_lines):
    ''' 返回对齐的比较块 '''
    
    rexp = r'@@ -(\w+),(\w+) \+(\w+),(\w+) @@'
    rexp_2 = r'@@ -(\w+) \+(\w+) @@'
    header = None
    lst1 = []
    lst2 = []
    ln1 = ln2 = -1
    delta_ln1 = delta_ln2 = 0
    for line in t_diff_lines:
        code = line[0]
        content = line[1:]
        if code == '@':
            if (len(lst1) + len(lst2)) > 0:
                yield header, lst1, lst2
                lst1 = []
                lst2 = []
            header = line       # update header
            match = re.match(rexp, header)
            if match:
                t_nums = match.groups()
                ln1 = int(t_nums[0])
                ln2 = int(t_nums[2])
            else:
                match = re.match(rexp_2, header)
		t_nums = match.groups()
                ln1 = int(t_nums[0])
                ln2 = int(t_nums[1])
            
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

    # yield last block
    fill_blank(delta_ln1, delta_ln2, lst1, lst2)
    yield header, lst1, lst2

    
# ==============================================================================
#  Compare tow lines
# ==============================================================================
def split_line_idxs(marker):
    ''' `marker` ==> diff marker by Python differ '''
    
    DIFF_DICT = {
        ' ' : 'same',
        '+' : 'add',
        '-' : 'remove',
        '^' : 'diff'
    }
    i = oi = 0
    oc = marker[0]
    slices = []
    for c in marker:
        if c != oc:
            # print '{%r}, [%d, %d, %r, %r]' % (marker, oi, i, oc, c)
            slices.append((DIFF_DICT[oc], oi, i))
            oc = c
            oi = i
        i += 1
    return slices

    
DIFFER = difflib.Differ()
def process_line_diff(line1, line2):
    text1, text2 = [line1], [line2]
    diffs = list(DIFFER.compare(text1, text2))
    diffs_len = len(diffs)

    for d in diffs:
        print '%r' % d
    print '='*80
    
    slices1, slices2 = None, None
    if diffs_len == 2:
        pass
    elif diffs_len == 3:
        if diffs[1].startswith('? '):
            marker1 = diffs[1][2:]
            slices1 = split_line_idxs(marker1)
        elif diffs[2].startswith('? '):
            marker2 = diffs[2][2:]
            slices2 = split_line_idxs(marker2)
        else:
            print diffs_len, line1, line2
            print '\n'.join(diffs)
            raise ValueError
    elif diffs_len == 4:
        marker1, marker2 = diffs[1][2:], diffs[3][2:]
        slices1 = split_line_idxs(marker1)
        slices2 = split_line_idxs(marker2)
    else:
        print diffs_len, line1, line2
        print '\n'.join(diffs)
        raise ValueError
        
    return line1, slices1, line2, slices2
        
#### [END] ####        


LINE_TYPE_DICT = {
    '#': 'fill',
    '==': 'same',
    '+': 'add',
    '!=': 'diff',
}

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
    ''' 处理一个块 '''
    # Format = u'%(ln)d:%(type)s:%(line)s'
    part1 = []
    part2 = []
    for i in range(len(lst1)):
        code1, ln1, content1 = lst1[i]
        code2, ln2, content2 = lst2[i]
        slices1, slices2 = None, None
        # print lst1[i]
        # print lst2[i]
        type1, type2 = get_type(code1, code2)
        if type1 == type2 == '!=' and content1 != content2:
            content1, slices1, content2, slices2 = process_line_diff(content1, content2)

        line1 = {'type': LINE_TYPE_DICT[type1]}
        line2 = {'type': LINE_TYPE_DICT[type2]}
        
        if type1 != '#':
            line1['ln'] = ln1
            line1['content'] = content1
            if slices1 is not None: line1['slices'] = slices1
        if type2 != '#':
            line2['ln'] = ln2
            line2['content'] = content2
            if slices2 is not None: line2['slices'] = slices2
            
        part1.append(line1)
        part2.append(line2)
        
    return part1, part2


HTML_FMT = '<span class="%s">%s</span>'
def default_line_processor(line):
    ''' build for HTML '''
    
    line_type = line['type']

    if line_type == 'fill':
        return line
    
    html = cgi.escape(line['content'])
    if line_type == 'diff' and 'slices' in line:
        content = line['content']
        parts = []
        for cls, start, end in line['slices']:
            part = content[start:end] if cls == 'same' else HTML_FMT % (cls, content[start:end])
            parts.append(part)
        last_slice_end = line['slices'][-1][-1]
        parts.append(content[last_slice_end:-1]) # Last part
        html = ''.join(parts)
        
    line['html'] = html
    return line
    
    
def parse_diff_blocks(data, line_processor=default_line_processor):
    _blocks = json.loads(data)
    return [[line_processor(line) for line in _block]
              for _block in _blocks]
    

def process_files_diff(filepath1, filepath2):
    diff_out = get_diff_output(filepath1, filepath2)
    diff_lines = diff_out.split('\n')

    rets1, rets2 = [], []
    for header, lst1, lst2 in get_aligned_blocks(diff_lines[2:]):
        # print header
        # print '--------------------'
        part1, part2 = process_block(lst1, lst2)
        if (len(part1) + len(part2)) > 0:
            rets1.append(part1)
            rets2.append(part2)
            
    data = {
        'blocks1': json.dumps(rets1),
        'blocks2': json.dumps(rets2),
        'html_result1': '',
        'html_result2': ''
    }
    
    return data

    
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
