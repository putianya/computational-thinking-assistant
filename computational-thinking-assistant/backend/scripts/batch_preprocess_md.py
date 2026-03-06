# -*- coding: utf-8 -*-
"""
批量 Markdown 预处理工具

功能：
- 扫描指定输入目录下所有 .md 文件
- 对每个文件调用 preprocess_md.split_md_to_files() 进行处理
- 输出到统一的 output_dir
- 支持 --prefix-by-file 参数：以原文件名（不含扩展名）作为前缀，避免不同文件章节名冲突

用法：
    python batch_preprocess_md.py <input_dir> [--output-dir <dir>] [--prefix-by-file] [--overwrite]

作者: 计算思维助手团队
日期: 2026-03-06
"""
import sys
import argparse
from pathlib import Path

# 确保可以导入同目录下的 preprocess_md 模块
sys.path.insert(0, str(Path(__file__).parent))
from preprocess_md import split_md_to_files


def batch_preprocess(
    input_dir: str,
    output_dir: str,
    prefix_by_file: bool = False,
    overwrite: bool = False,
) -> int:
    """
    批量处理输入目录下所有 .md 文件。

    Args:
        input_dir: 包含原始 Markdown 文件的目录路径
        output_dir: 所有输出文件的统一目标目录
        prefix_by_file: 若为 True，以原文件名（不含扩展名）作为前缀
        overwrite: 若为 True，同名文件直接覆盖；否则询问用户

    Returns:
        int: 总输出文件数量
    """
    input_dir_path = Path(input_dir)

    if not input_dir_path.exists() or not input_dir_path.is_dir():
        print(f"❌ 输入目录不存在或不是目录: {input_dir}")
        return 0

    # 扫描所有 .md 文件
    md_files = sorted(input_dir_path.glob('*.md'))

    if not md_files:
        print(f"⚠️  目录中没有找到 .md 文件: {input_dir}")
        return 0

    total_files = len(md_files)
    total_output = 0

    for idx, md_file in enumerate(md_files, 1):
        # 决定前缀
        if prefix_by_file:
            prefix = md_file.stem + '_'
        else:
            prefix = ''

        print(f"\n📄 [{idx}/{total_files}] 处理: {md_file.name}")

        output_files = split_md_to_files(
            input_path=str(md_file),
            output_dir=output_dir,
            prefix=prefix,
            overwrite=overwrite,
        )

        count = len(output_files)
        total_output += count
        print(f"   -> 输出 {count} 个文件")

    return total_output


def main():
    """
    命令行入口，支持：
        python batch_preprocess_md.py <input_dir> [--output-dir <dir>] [--prefix-by-file] [--overwrite]
    """
    parser = argparse.ArgumentParser(
        description='批量 Markdown 预处理工具：扫描目录并将所有 .md 文件按章节分割为标准格式',
    )
    parser.add_argument('input_dir', help='包含原始 Markdown 文件的目录路径')
    parser.add_argument(
        '--output-dir',
        default=None,
        help='输出目录（默认为脚本所在目录的 ../data/knowledge/）',
    )
    parser.add_argument(
        '--prefix-by-file',
        action='store_true',
        help='以原文件名（不含扩展名）作为输出文件名前缀，避免章节名冲突',
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='若输出文件已存在则直接覆盖，不询问',
    )
    args = parser.parse_args()

    # 确定输出目录
    if args.output_dir:
        output_dir = Path(args.output_dir).resolve()
    else:
        script_dir = Path(__file__).parent
        output_dir = (script_dir / '..' / 'data' / 'knowledge').resolve()

    input_dir = Path(args.input_dir).resolve()

    print('=' * 40)
    print(f'📂 批量处理目录: {input_dir}/')
    print(f'📂 输出目录: {output_dir}/')
    print('=' * 40)

    total_output = batch_preprocess(
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        prefix_by_file=args.prefix_by_file,
        overwrite=args.overwrite,
    )

    # 统计输入文件数量
    md_files = list(Path(input_dir).glob('*.md')) if Path(input_dir).exists() else []

    print('\n' + '=' * 40)
    print(
        f'🎉 批量处理完成！共处理 {len(md_files)} 个文件，输出 {total_output} 个知识库文件'
    )
    print('=' * 40)


if __name__ == '__main__':
    main()
