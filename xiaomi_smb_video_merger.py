import os
import re
import sys
import subprocess
import tempfile
import shutil
from datetime import datetime
from smb.SMBConnection import SMBConnection
import sys
import io
import functools
import argparse

# 设置输出编码
print = functools.partial(print, flush=True)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 解析命令行参数
parser = argparse.ArgumentParser(description='小米摄像头视频合并工具')
parser.add_argument('-v', '--verbose', action='store_true', help='显示详细日志')
parser.add_argument('--test-download', action='store_true', help='测试安装ffmpeg-python模块功能')
args = parser.parse_args()

# 是否显示详细日志
VERBOSE = args.verbose

# 自定义日志函数
def log(message, level="INFO"):
    """输出日志信息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def debug(message):
    """输出调试信息，仅在详细模式下显示"""
    if VERBOSE:
        log(message, "DEBUG")
# SMB连接信息
SMB_SERVER = '10.10.10.2'
SMB_SHARE = 'xiaomisxt'
SMB_PATH = 'xiaomi_camera_videos/607EA4901FA8'
SMB_USERNAME = '245623580'
SMB_PASSWORD = 'yang8687123'

# 本地临时目录
TEMP_DIR = tempfile.gettempdir()

# 脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def connect_to_smb():
    """连接到SMB服务器"""
    try:
        # 创建SMB连接
        conn = SMBConnection(SMB_USERNAME, SMB_PASSWORD, 'client', SMB_SERVER, use_ntlm_v2=True)
        if not conn.connect(SMB_SERVER, 139):
            print(f"无法连接到SMB服务器 {SMB_SERVER}")
            return None
        return conn
    except Exception as e:
        print(f"连接SMB服务器时出错: {e}")
        return None

def list_folders(conn):
    """列出指定路径下的所有文件夹"""
    try:
        folders = []
        file_list = conn.listPath(SMB_SHARE, SMB_PATH)
        for item in file_list:
            if item.isDirectory and item.filename not in ['.', '..']:
                # 检查文件夹名称是否符合日期时间格式（如2025031205）
                if re.match(r'^\d{10}$', item.filename):
                    folders.append(item.filename)
        # 按照日期时间排序
        folders.sort()
        return folders
    except Exception as e:
        print(f"列出文件夹时出错: {e}")
        return []

def list_mp4_files(conn, folder):
    """列出指定文件夹中的所有MP4文件"""
    try:
        mp4_files = []
        folder_path = f"{SMB_PATH}/{folder}"
        file_list = conn.listPath(SMB_SHARE, folder_path)
        for item in file_list:
            if not item.isDirectory and item.filename.lower().endswith('.mp4') and item.filename != 'merged.mp4':
                mp4_files.append(item.filename)
        # 当只有一个文件时跳过处理
        if len(mp4_files) == 1:
            return []
        # 按文件名排序
        mp4_files.sort()
        return mp4_files
    except Exception as e:
        print(f"列出MP4文件时出错: {e}")
        return []

def download_file(conn, remote_folder, filename, local_folder):
    """从SMB服务器下载文件到本地临时目录"""
    try:
        remote_path = f"{SMB_PATH}/{remote_folder}/{filename}"
        local_path = os.path.join(local_folder, filename)
        
        with open(local_path, 'wb') as file_obj:
            conn.retrieveFile(SMB_SHARE, remote_path, file_obj)
        
        return local_path
    except Exception as e:
        print(f"下载文件 {filename} 时出错: {e}")
        return None

def check_ffmpeg_python_installation():
    """检查并尝试安装ffmpeg-python模块"""
    try:
        # 尝试导入ffmpeg-python模块
        import ffmpeg
        log("ffmpeg-python模块已安装", "SUCCESS")
        return True
    except ImportError:
        # 如果模块未安装，尝试自动安装
        log("ffmpeg-python模块未安装，尝试自动安装...", "WARNING")
        try:
            import subprocess
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'ffmpeg-python'], 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            if result.returncode == 0:
                log("ffmpeg-python模块安装成功", "SUCCESS")
                # 重新导入模块
                try:
                    import ffmpeg
                    return True
                except ImportError:
                    log("安装后仍无法导入ffmpeg-python模块", "ERROR")
            else:
                error = result.stderr.decode() if result.stderr else "未知错误"
                log(f"安装ffmpeg-python模块失败: {error}", "ERROR")
        except Exception as e:
            log(f"尝试安装ffmpeg-python模块时出错: {e}", "ERROR")
        
        # 提供手动安装指南
        log("\n[Python依赖错误] 无法自动安装ffmpeg-python模块", "ERROR")
        log("请手动安装ffmpeg-python模块:")
        log("1. 打开命令提示符或终端")
        log("2. 运行命令: pip install ffmpeg-python")
        log("3. 安装完成后重新运行此程序")
        return False

def check_ffmpeg_python():
    """检查ffmpeg-python模块是否安装正确"""
    try:
        import ffmpeg
        # 验证模块功能完整性
        if not hasattr(ffmpeg, 'probe'):
            raise AttributeError()
        return True
    except ImportError:
        log("\n[Python依赖错误] 缺少ffmpeg-python模块", "ERROR")
        log("安装命令: pip install ffmpeg-python", "ERROR")
        return False
    except AttributeError:
        log("\n[版本兼容错误] ffmpeg-python模块版本不兼容", "ERROR")
        log("升级命令: pip install --upgrade ffmpeg-python", "ERROR")
        return False


def check_ffmpeg_python():
    """检查ffmpeg-python模块是否安装正确"""
    try:
        import ffmpeg
        # 验证模块功能完整性
        if not hasattr(ffmpeg, 'probe'):
            raise AttributeError()
        return True
    except ImportError:
        print("\n[Python依赖错误] 缺少ffmpeg-python模块")
        print("安装命令: pip install ffmpeg-python")
        return False
    except AttributeError:
        print("\n[版本兼容错误] ffmpeg-python模块版本不兼容")
        print("升级命令: pip install --upgrade ffmpeg-python")
        return False

def check_ffmpeg_executable():
    # 新增环境变量检查路径
    search_paths = [
        os.path.join(SCRIPT_DIR, 'ffmpeg'),
        os.path.join(SCRIPT_DIR, 'ffmpeg.exe'),
        os.path.join(SCRIPT_DIR, 'ffmpeg.zip')
    ]
    """检查ffmpeg可执行文件是否存在，如果不存在则尝试解压ffmpeg.zip
    
    Returns:
        bool: ffmpeg可执行文件是否可用
    """
    try:
        # 首先检查系统PATH中是否有ffmpeg
        try:
            # 使用subprocess检查ffmpeg命令是否可用
            result = subprocess.run(['ffmpeg', '-version'], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   check=False)
            if result.returncode == 0:
                debug("系统中已安装ffmpeg")
                return True
        except Exception:
            debug("系统PATH中未找到ffmpeg")
        
        # 检查脚本目录下是否有ffmpeg.exe
        ffmpeg_exe_path = os.path.join(SCRIPT_DIR, 'ffmpeg.exe')
        if os.path.exists(ffmpeg_exe_path):
            debug(f"找到ffmpeg可执行文件: {ffmpeg_exe_path}")
            # 将ffmpeg所在目录添加到环境变量PATH中
            os.environ['PATH'] = SCRIPT_DIR + os.pathsep + os.environ['PATH']
            return True
        
        # 检查是否有ffmpeg.zip文件，如果有则解压
        ffmpeg_zip_path = os.path.join(SCRIPT_DIR, 'ffmpeg.zip')
        if os.path.exists(ffmpeg_zip_path):
            log("找到ffmpeg.zip文件，尝试解压...")
            try:
                # 创建临时目录用于解压
                ffmpeg_extract_dir = os.path.join(TEMP_DIR, 'ffmpeg_extract')
                os.makedirs(ffmpeg_extract_dir, exist_ok=True)
                
                # 使用Python的zipfile模块解压文件
                import zipfile
                with zipfile.ZipFile(ffmpeg_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(ffmpeg_extract_dir)
                
                # 查找解压后的ffmpeg.exe文件
                for root, dirs, files in os.walk(ffmpeg_extract_dir):
                    if 'ffmpeg.exe' in files:
                        ffmpeg_exe_path = os.path.join(root, 'ffmpeg.exe')
                        debug(f"从zip文件中提取到ffmpeg: {ffmpeg_exe_path}")
                        # 将ffmpeg所在目录添加到环境变量PATH中
                        os.environ['PATH'] = os.path.dirname(ffmpeg_exe_path) + os.pathsep + os.environ['PATH']
                        return True
                
                log("在解压的文件中未找到ffmpeg.exe", "ERROR")
            except Exception as e:
                log(f"解压ffmpeg.zip时出错: {e}", "ERROR")
        
        log(f"未找到ffmpeg可执行文件，请执行以下操作之一:\n1. 从官网下载ffmpeg并配置环境变量 (https://ffmpeg.org/download.html)\n2. 将包含ffmpeg.exe的zip文件重命名为ffmpeg.zip放在脚本目录\n当前脚本目录: {SCRIPT_DIR}", "ERROR")
        return False
    except Exception as e:
        log(f"检查ffmpeg可执行文件时出错: {e}", "ERROR")
        return False

def merge_videos(video_files, output_file):
    """使用ffmpeg-python模块合并视频文件
    
    Args:
        video_files: 要合并的视频文件列表
        output_file: 合并后的输出文件路径
        
    Returns:
        bool: 合并是否成功
    """
    # 检查ffmpeg-python模块是否可用
    if not check_ffmpeg_python():
        return False
    
    # 检查ffmpeg可执行文件是否可用
    if not check_ffmpeg_executable():
        return False
    
    # 检查输入文件是否存在
    for video_file in video_files:
        if not os.path.exists(video_file):
            log(f"错误: 文件不存在: {video_file}", "ERROR")
            return False
    
    if len(video_files) == 0:
        log("错误: 没有提供视频文件", "ERROR")
        return False
    
    list_file_path = None
    try:
        # 导入ffmpeg-python模块
        import ffmpeg
        
        log(f"开始合并 {len(video_files)} 个视频文件...")
        
        # 创建一个临时文件列表 - 这是ffmpeg concat demuxer所需的
        list_file_path = os.path.join(TEMP_DIR, f'file_list_{datetime.now().strftime("%Y%m%d%H%M%S")}.txt')
        with open(list_file_path, 'w', encoding='utf-8') as f:
            for video_file in video_files:
                # 确保路径使用正确的转义
                escaped_path = video_file.replace('\\', '\\\\')
                f.write(f"file '{escaped_path}'\n")
        
        debug(f"临时文件列表创建成功: {list_file_path}")
        debug(f"文件列表内容: {open(list_file_path, 'r').read() if os.path.exists(list_file_path) else '文件不存在'}")
        
        try:
            # 使用concat demuxer合并视频
            # 这种方式适用于相同编码的MP4文件
            input_stream = ffmpeg.input(list_file_path, format='concat', safe=0)
            output_stream = ffmpeg.output(input_stream, output_file, codec='copy', loglevel='warning')
            output_stream = ffmpeg.overwrite_output(output_stream)
            
            # 运行ffmpeg并捕获输出
            log("执行ffmpeg合并操作...")
            try:
                # 尝试获取ffmpeg命令行
                cmd = ffmpeg.compile(output_stream)
                debug(f"ffmpeg命令: {' '.join(cmd)}")
            except Exception as e:
                debug(f"无法获取ffmpeg命令: {e}")
            
            ffmpeg.run(output_stream, capture_stdout=True, capture_stderr=True)
            
            # 验证输出文件是否创建成功
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                log(f"视频合并成功完成，输出文件: {output_file}", "SUCCESS")
                return True
            else:
                log(f"错误: 输出文件创建失败或为空: {output_file}", "ERROR")
                return False
                
        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if hasattr(e, 'stderr') and e.stderr else str(e)
            log(f"ffmpeg处理时出错: {error_message}", "ERROR")
            return False
    
    except ImportError:
        log("错误: 无法导入ffmpeg-python模块，请确保已正确安装", "ERROR")
        log("安装方法: pip install ffmpeg-python", "ERROR")
        return False
    except Exception as e:
        log(f"合并视频时出错: {e}", "ERROR")
        return False
    finally:
        # 删除临时文件列表
        if list_file_path and os.path.exists(list_file_path):
            try:
                os.remove(list_file_path)
                debug("已清理临时文件")
            except Exception as e:
                log(f"清理临时文件时出错: {e}", "ERROR")


def upload_file(conn, local_file, remote_folder):
    """将合并后的文件上传到SMB服务器"""
    try:
        remote_path = f"{SMB_PATH}/{remote_folder}/merged.mp4"
        with open(local_file, 'rb') as file_obj:
            conn.storeFile(SMB_SHARE, remote_path, file_obj)
        return True
    except Exception as e:
        print(f"上传文件时出错: {e}")
        return False

def process_folder(conn, folder):
    """处理单个文件夹中的视频文件
    
    Args:
        conn: SMB连接对象
        folder: 要处理的文件夹名称
    """
    print(f"\n处理文件夹: {folder}")
    
    # 创建临时目录
    temp_folder = os.path.join(TEMP_DIR, folder)
    os.makedirs(temp_folder, exist_ok=True)
    
    try:
        # 列出文件夹中的MP4文件
        mp4_files = list_mp4_files(conn, folder)
        if not mp4_files:
            print(f"文件夹 {folder} 中没有MP4文件")
            return
        
        print(f"找到 {len(mp4_files)} 个MP4文件")
        
        # 下载所有MP4文件
        local_files = []
        download_failed = 0
        for mp4_file in mp4_files:
            print(f"下载文件: {mp4_file}")
            local_file = download_file(conn, folder, mp4_file, temp_folder)
            if local_file:
                local_files.append(local_file)
            else:
                download_failed += 1
        
        if not local_files:
            print("没有成功下载任何文件")
            return
        
        if download_failed > 0:
            print(f"警告: {download_failed} 个文件下载失败")
        
        # 合并视频文件
        output_file = os.path.join(temp_folder, "merged.mp4")
        print(f"开始合并 {len(local_files)} 个视频文件到 {output_file}...")
        
        # 调用优化后的merge_videos函数
        if merge_videos(local_files, output_file):
            print("视频合并成功")
            
            # 检查输出文件
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
                print(f"合并后的文件大小: {file_size_mb:.2f} MB")
                
                # 上传合并后的文件
                print("上传合并后的文件...")
                if upload_file(conn, output_file, folder):
                    print("文件上传成功")
                    # 删除原始文件
                    print("正在清理原始文件...")
                    for mp4_file in mp4_files:
                        try:
                            remote_path = f"{SMB_PATH}/{folder}/{mp4_file}"
                            conn.deleteFiles(SMB_SHARE, remote_path)
                            debug(f"已删除原始文件: {mp4_file}")
                        except Exception as del_error:
                            print(f"删除文件 {mp4_file} 失败: {del_error}")
                else:
                    print("文件上传失败")
            else:
                print("错误: 合并后的文件不存在或为空")
        else:
            print("视频合并失败")
    
    except Exception as e:
        print(f"处理文件夹 {folder} 时出错: {e}")
        import traceback
        print(traceback.format_exc())
    
    finally:
        # 清理临时文件
        try:
            if os.path.exists(temp_folder):
                print(f"清理临时目录: {temp_folder}")
                shutil.rmtree(temp_folder)
        except Exception as e:
            print(f"清理临时文件时出错: {e}")

def main():
    log("开始处理视频文件...")
    
    # 如果是测试下载模式，只测试安装ffmpeg-python模块
    if args.test_download:
        log("测试安装ffmpeg-python模块模式")
        if check_ffmpeg_python_installation():
            log("ffmpeg-python模块安装测试成功", "SUCCESS")
        else:
            log("ffmpeg-python模块安装测试失败", "ERROR")
        return
    
    # 检查ffmpeg-python模块
    if not check_ffmpeg_python():
        log("ffmpeg-python模块不可用，尝试自动安装", "WARNING")
        if not check_ffmpeg_python_installation():
            log("无法安装ffmpeg-python模块，程序无法继续运行", "ERROR")
            return
    
    # 连接到SMB服务器
    conn = connect_to_smb()
    if not conn:
        return
    
    try:
        # 列出所有文件夹
        folders = list_folders(conn)
        if not folders:
            log(f"在路径 {SMB_PATH} 下没有找到符合条件的文件夹", "WARNING")
            return
        
        log(f"找到 {len(folders)} 个文件夹")
        
        # 处理每个文件夹
        for folder in folders:
            process_folder(conn, folder)
    
    finally:
        # 关闭SMB连接
        conn.close()
    
    log("\n所有文件夹处理完成", "SUCCESS")

if __name__ == "__main__":
    main()
