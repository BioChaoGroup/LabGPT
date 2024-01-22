# Generate a document for this project
# 项目文档
## BIGPT
This is BioinformaticsGPT powered by ChatGPT.  

Currently I just written a simple code to automatically summarize recent papers in bioinformatics from Nature series journal and then generate a post to my hexo blog website.

## Usage

### 1. Install the required packages
- [metaGPT](https://github.com/geekan/MetaGPT) >= 0.6.0
- [hexo](https://hexo.io)

More resource for metaGPT:
- **「学习手册」**：[https://deepwisdom.feishu.cn/docx/UBoydfLRXodYjdxPKeyc9QWhnvW](https://deepwisdom.feishu.cn/docx/UBoydfLRXodYjdxPKeyc9QWhnvW)
- **「教程地址」**：[https://deepwisdom.feishu.cn/docx/RJmTdvZuPozAxFxEpFxcbiPwnQf](https://deepwisdom.feishu.cn/docx/RJmTdvZuPozAxFxEpFxcbiPwnQf)
- **「常见问题」**：[https://deepwisdom.feishu.cn/docx/WFtJdRUsaosTx0x1JgacEK3Znge](https://deepwisdom.feishu.cn/docx/WFtJdRUsaosTx0x1JgacEK3Znge)

A Step-by-Step Guide on Building a Hexo Blog Website:
- **「[快速搭建个人博客——保姆级教程](https://pdpeng.github.io/2022/01/19/setup-personal-blog/)」** by 攻城狮杰森

### 2. clone this simple repo

```
git clone https://github.com/biochaoGroup/BIGPT.git
```

My step-by-step thinking about this agent:
- **[MetaGPT学习笔记「03.制作订阅智能体」](https://zhuanlan.zhihu.com/p/678687197)**

### 3. Configure

Put your hexo local repo in config.yaml. I will suggest this location:
```
$HOME/.metagpt/config.yaml
```

Add following key:
```
### Custom hexo dir
HEXO_LOCAL_DIR: "$HOME/path/to/hexo-blog"
```


### 4. Run

```
python main.py
```

# Feeback
If you have any questions, please feel free to contact me.
