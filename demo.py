#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bib-Sanitizer 功能演示脚本

这个脚本演示了 Bib-Sanitizer 的核心功能，无需真实的 API 调用。
"""

from colorama import init, Fore, Style

init(autoreset=True)


def print_header(title):
    """打印标题"""
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{title:^60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")


def demo_auto_update():
    """演示自动更新功能"""
    print_header("功能 1: 自动更新 arXiv 条目")
    
    print(f"{Fore.YELLOW}[输入] arXiv-only 条目:{Style.RESET_ALL}")
    print("""
@article{example_arxiv,
  title={Deep Learning for Computer Vision: A Survey},
  author={Zhang, Wei and Li, Ming},
  journal={arXiv preprint arXiv:2101.12345},
  year={2021}
}
""")
    
    print(f"{Fore.GREEN}[输出] 更新后的条目:{Style.RESET_ALL}")
    print("""
@inproceedings{example_arxiv,
  title={Deep Learning for Computer Vision: A Survey},
  author={Zhang, Wei and Li, Ming},
  booktitle={CVPR},
  year={2021},
  doi={10.1109/CVPR.2021.12345}
}
""")
    
    print(f"{Fore.CYAN}[说明]{Style.RESET_ALL}")
    print("  • 检测到该论文在 CVPR 2021 正式发表")
    print("  • 将 journal (arXiv) 更新为 booktitle (CVPR)")
    print("  • 添加了 DOI")
    print("  • 移除了 arXiv 相关字段")


def demo_format_clean():
    """演示格式清理功能"""
    print_header("功能 2: 统一会议名称格式")
    
    print(f"{Fore.YELLOW}[输入] 冗长的会议名称:{Style.RESET_ALL}")
    print("""
@inproceedings{example_long_name,
  title={Attention is All You Need},
  author={Vaswani, Ashish and others},
  booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition},
  year={2017}
}
""")
    
    print(f"{Fore.GREEN}[输出] 统一后的格式:{Style.RESET_ALL}")
    print("""
@inproceedings{example_long_name,
  title={Attention is All You Need},
  author={Vaswani, Ashish and others},
  booktitle={CVPR},
  year={2017}
}
""")
    
    print(f"{Fore.CYAN}[说明]{Style.RESET_ALL}")
    print("  • 将冗长的会议全称统一为简称 CVPR")
    print("  • 支持多种变体的自动识别")
    print("  • 可通过配置文件自定义映射规则")


def demo_link_check():
    """演示链接检查功能"""
    print_header("功能 3: 检查链接可用性")
    
    print(f"{Fore.YELLOW}[检查] 条目中的链接:{Style.RESET_ALL}")
    print("""
@article{example_with_links,
  title={An Example Paper},
  url={https://example.com/paper.pdf},
  pdf={https://arxiv.org/pdf/2101.12345.pdf}
}
""")
    
    print(f"{Fore.GREEN}[结果] 链接状态报告:{Style.RESET_ALL}")
    print(f"  ✓ {Fore.GREEN}pdf: https://arxiv.org/pdf/2101.12345.pdf - OK{Style.RESET_ALL}")
    print(f"  ✗ {Fore.RED}url: https://example.com/paper.pdf - HTTP 404 Not Found{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}[说明]{Style.RESET_ALL}")
    print("  • 检查所有 url 和 pdf 字段的链接")
    print("  • 先尝试 HEAD 请求，失败则用 GET")
    print("  • 支持超时和重试配置")
    print("  • 生成详细的失效链接报告")


def demo_report():
    """演示报告输出"""
    print_header("综合报告示例")
    
    print(f"{Fore.GREEN}[更新] 成功更新 2 个条目:{Style.RESET_ALL}")
    print(f"  - {Fore.CYAN}zhang2021deep{Style.RESET_ALL}: article → inproceedings")
    print(f"    • venue: arXiv preprint... → CVPR")
    print(f"    • year: 2021 → 2021")
    
    print(f"\n{Fore.GREEN}[格式] 统一了 3 处格式:{Style.RESET_ALL}")
    print(f"  - {Fore.CYAN}vaswani2017attention{Style.RESET_ALL}.booktitle: Proceedings of... → CVPR")
    print(f"  - {Fore.CYAN}he2016resnet{Style.RESET_ALL}.booktitle: IEEE Conference... → CVPR")
    print(f"  - {Fore.CYAN}lecun2015deep{Style.RESET_ALL}.journal: Neural Info... → NeurIPS")
    
    print(f"\n{Fore.RED}[链接] 发现 1 个失效链接:{Style.RESET_ALL}")
    print(f"  - {Fore.CYAN}smith2020example{Style.RESET_ALL}.url: https://example.com/paper.pdf")
    print(f"    状态: HTTP 404 Not Found")
    
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}统计信息:{Style.RESET_ALL}")
    print(f"  • 更新条目: 2")
    print(f"  • 格式变更: 3")
    print(f"  • 失效链接: 1")
    print(f"  • 错误: 0")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")


def main():
    """主函数"""
    print(f"\n{Fore.GREEN}{'*'*60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Bib-Sanitizer 功能演示{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'*'*60}{Style.RESET_ALL}")
    
    demo_auto_update()
    input(f"\n{Fore.YELLOW}按 Enter 继续...{Style.RESET_ALL}")
    
    demo_format_clean()
    input(f"\n{Fore.YELLOW}按 Enter 继续...{Style.RESET_ALL}")
    
    demo_link_check()
    input(f"\n{Fore.YELLOW}按 Enter 继续...{Style.RESET_ALL}")
    
    demo_report()
    
    print(f"\n{Fore.GREEN}{'*'*60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}演示结束！{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'*'*60}{Style.RESET_ALL}\n")
    
    print(f"{Fore.CYAN}现在可以尝试真实的功能:{Style.RESET_ALL}")
    print(f"  python bib_sanitizer.py examples/sample.bib --all --dry-run")


if __name__ == '__main__':
    main()
