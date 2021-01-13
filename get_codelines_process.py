# -*- coding: utf-8 -*
import os, string
import time
import multiprocessing
from tkinter import *
from tkinter.filedialog import askdirectory

def python_lines_count(file_path,encoding):
    lines_count_python = 0
    flag_python = 0  # 定义标志位，用于跳过多行注释的代码
    try:
        with open(file_path, "r", encoding=encoding) as fp:
            for line in fp:
                if line.strip() == "'''" or line.strip()[1:4] == "'''" or line.strip()[
                                                                          -3:] == "'''":  # 多行注释，行首或行尾为三引号'''，文件首行第一个有可能为BOM字符
                    flag_python += 1  # 遇到多行注释的开头，flag_python+1变为奇数，遇到多行注释的结尾，flag_python+1变为偶数
                elif flag_python % 2 != 0:  # flag_python为奇数时，说明当前行为多行注释内的代码，所以不进行代码统计，直到flag_python变为偶数后，才开始统计
                    continue
                elif line.strip() in string.whitespace:  # 空白行
                    pass
                elif line.lstrip()[0] == "#" or line.lstrip()[1] == "#":  # 单行注释,当在首行时，第一个字符有可能是BOM字符
                    pass
                else:
                    lines_count_python += 1  # 当前行，是非多行注释、单行注释、空行的情况，统计的代码行数+1
        return lines_count_python
    except Exception as e:
        print(e)
        return 0

def java_c_lines_count(file_path,encoding):
    lines_count_java_c = 0
    flag_java = 0
    try:
        with open(file_path, "r", encoding=encoding) as fp:
            for line in fp:
                if line.strip()[:2] == "/*" or line.strip()[-2:] == "*/":  # java和 C语言的多行注释
                    flag_java += 1
                elif flag_java % 2 != 0:
                    continue
                elif line.strip() in string.whitespace:  # 空行
                    pass
                elif line.lstrip()[:2] == "//":  ##java和 C语言的单行注释
                    pass
                else:
                    lines_count_java_c += 1
        return lines_count_java_c
    except Exception as e:
        print(e)
        return 0
def get_files_path(dir_path,queue): #遍历目录下的所有文件，并将python，java，C源码文件的绝对路径放到一个队列里
    for root, dirs, files in os.walk(dir_path):
        for file in files:#遍历目录下的所有文件
            if os.path.splitext(file)[1] in [".py",".java",".c"]: #根据文件后缀判断文件类型
                file_path = os.path.join(root,file) #拼接代码文件绝对路径
                queue.put(file_path)    #将代码文件的绝对路径放到队列里

def get_code_lines(queue,total_count_python,total_count_java,total_count_c):  # 从队列中获取文件，并统计代码行数
    while not queue.empty():
        file_path = queue.get()
        file_path_suffix = os.path.splitext(file_path)[1] #获取代码文件的后缀
        if file_path_suffix == ".py": #后缀为.py，则为python代码文件
            try:
                lines_count_python = python_lines_count(file_path,"utf-8")  #使用utf-8编码打开python文件
            except:
                lines_count_python = python_lines_count(file_path, "gbk")   #python文件大部分是utf-8或者gbk格式，当使用utf-8编码打开文件报错后，再使用gbk编码打开文件，进行代码统计
            total_count_python.value += lines_count_python
        elif file_path_suffix in [".java",".c"]: #根据后缀判断java或c文件
            lines_count_java_c = java_c_lines_count(file_path,"utf-8")      #使用utf-8编码打开java文件或者c文件
            if file_path_suffix == ".java":
                total_count_java.value += lines_count_java_c
            elif file_path_suffix == ".c":
                total_count_c.value += lines_count_java_c
    return


def get_total_code_lines(dir_path):#使用多进程与队列，实现代码行数统计
    start = time.time()
    queue = multiprocessing.Queue(1000)     #定义一个队列，用于存取代码文件的绝对路径
    total_count_python = multiprocessing.Value("d", 0)  # python代码总行数，d表示数值,主进程与子进程共享这个value。（主进程与子进程都是用的同一个value）
    total_count_java = multiprocessing.Value("d", 0)    # java代码总行数
    total_count_c = multiprocessing.Value("d", 0)       # c语言代码总行数
    p_get_path = multiprocessing.Process(target=get_files_path,args=(dir_path,queue)) #创建一个进程，用于获取所有的代码文件绝对路径
    p_get_path.start() #启动进程
    num_cpu = multiprocessing.cpu_count()  # 获取当前计算机的cpu核数
    p_get_lindes = [ multiprocessing.Process(target=get_code_lines,args=(queue,total_count_python,total_count_java,total_count_c)) for i in range(num_cpu)] #创建多个进程，计算每个文件的代码行数
    for p in p_get_lindes:#循环启动进程
        p.start()
        p.join()
    p_get_path.join() #执行join方法，待子进程全部结束后，再执行主进程的之后的代码逻辑

    print("python代码总行数：",int(total_count_python.value))
    print("java代码总行数：", int(total_count_java.value))
    print("c语言代码总行数：", int(total_count_c.value))
    end = time.time()
    tatal_time = end - start  #计算统计代码的总耗时
    print("总耗时：",tatal_time)
    return int(total_count_python.value),int(total_count_java.value),int(total_count_c.value),tatal_time

def selectPath():#点击“选择”按钮，可进行选取文件夹操作，并获取文件夹路径
    path_ = askdirectory()  #获取文件夹路径
    path.set(path_)         #StringVar变量的值更新为获取的文件夹路径

def click_submit(): #点击“开始统计”按钮，触发代码统计，并更新统计结果
    dir_path=path.get() #获取文本框中的目录路径
    total_line_count = get_total_code_lines(dir_path) # 调用统计代码方法，获取各类型代码行数
    total_count_python.set(str(total_line_count[0]))  # 将统计的python代码行数更新并展示到文本框内
    total_count_java.set(str(total_line_count[1]))    # 将统计的java代码行数更新并展示到文本框内
    total_count_c.set(str(total_line_count[2]))       # 将统计的C语言代码行数更新并展示到文本框内
    total_time.set("%.3f" %total_line_count[3])       # 将总耗时更新并展示到文本框内

def add_Label_Entry(row,text,textvariable): #在同一行，分别创建标签和文本框
    Label(windows, text=text).grid(row=row, column=2,ipadx=5, pady=5) #创建标签，用于显示代码类型
    Entry(windows, textvariable=textvariable).grid(row=row, column=3,ipadx=5, pady=5) #创建文本框，用于展示统计的代码行数


if __name__ == '__main__':
    windows = Tk()
    windows.title("统计代码行工具")  #设置标题
    windows.geometry("400x400")     #设置大小
    path = StringVar()
    total_count_python = StringVar()
    total_count_java = StringVar()
    total_count_c = StringVar()
    total_time = StringVar()

    Label(windows,text = "代码行统计路径:").grid(row = 10, column = 2,ipadx=5, pady=50)
    Entry(windows, textvariable=path).grid(row=10, column=3,ipadx=20, pady=20)
    Button(windows, text="选择", command=selectPath).grid(row=10, column=4,ipadx=20, pady=20) #创建“选择”按钮,并定义点击事件

    Button(windows, text="开始统计", command=click_submit).grid(row=20, column=3,ipadx=60, pady=30) #创建“开始统计”按钮，并定义点击事件
    add_Label_Entry(60,"python代码总行数:",total_count_python) #在同一行，创建标签和文本框，用于展示python代码总行数
    add_Label_Entry(70, "java代码总行数:",total_count_java)  # 在同一行，创建标签和文本框，用于展示java代码总行数
    add_Label_Entry(80, "C语言代码总行数:",total_count_c)  # 在同一行，创建标签和文本框，用于展示C语言代码总行数
    add_Label_Entry(90, "总耗时(s):",total_time)  # 在同一行，创建标签和文本框，用于展示统计代码行数总耗时

    windows.mainloop()


