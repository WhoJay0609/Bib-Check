#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bib-Check 功能演示脚本

这个脚本演示了 Bib-Check 的核心功能，无需真实的 API 调用。
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


def demo_link_check():
    """演示链接检查功能"""
    print_header("功能 2: 检查链接可用性")
    
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
    
    print(f"\n{Fore.GREEN}[作者] 截断了 2 个条目:{Style.RESET_ALL}")
    print(f"  - {Fore.CYAN}brown2020language{Style.RESET_ALL}: Tom B. Brown and ... → Tom B. Brown et. al")
    print(f"  - {Fore.CYAN}kaplan2020scaling{Style.RESET_ALL}: Jared Kaplan and ... → Jared Kaplan et. al")
    
    print(f"\n{Fore.RED}[链接] 发现 1 个失效链接:{Style.RESET_ALL}")
    print(f"  - {Fore.CYAN}smith2020example{Style.RESET_ALL}.url: https://example.com/paper.pdf")
    print(f"    状态: HTTP 404 Not Found")
    
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}统计信息:{Style.RESET_ALL}")
    print(f"  • 更新条目: 2")
    print(f"  • 作者截断: 2")
    print(f"  • 失效链接: 1")
    print(f"  • 错误: 0")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")


def main():
    """主函数"""
    print(f"\n{Fore.GREEN}{'*'*60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Bib-Check 功能演示{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'*'*60}{Style.RESET_ALL}")
    
    demo_auto_update()
    input(f"\n{Fore.YELLOW}按 Enter 继续...{Style.RESET_ALL}")
    
    demo_link_check()
    input(f"\n{Fore.YELLOW}按 Enter 继续...{Style.RESET_ALL}")
    
    demo_report()
    
    print(f"\n{Fore.GREEN}{'*'*60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}演示结束！{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'*'*60}{Style.RESET_ALL}\n")
    
    print(f"{Fore.CYAN}现在可以尝试真实的功能:{Style.RESET_ALL}")
    print(f"  python bib_check.py examples/sample.bib --all --dry-run")


if __name__ == '__main__':
    main()
