#  基于病虫害知识图谱的问答

## Rasa使用教程

详见官方文档[Introduction to Rasa Open Source & Rasa Pro](https://rasa.com/docs/rasa/)

## 项目介绍

data/nlu.yaml中存放训练数据

## Rasa 版本和项目依赖

本项目所用代码在 Rasa 3.0.X 版本中完成。
可以使用：

```shell
pip install requirements.txt
```

完成项目代码的依赖安装。

## 训练 Rasa 模型

```bash
rasa train
```

## 启动 Rasa 动作服务器

```shell
rasa run actions
```

## 启动 Rasa 服务器

```bash
rasa run --cors "*"
```

## 启动网页客户端

```bash
python -m http.server
```

使用浏览器打开链接: [http://localhost:8000/](http://localhost:8000/)

## 操作过程

![image-20231113153423256](media\image-20231113153423256.png)

在用户输入“你好”后会给出几个可供选择的问题，可以选择或自定义问题。
提问方式：首先针对要提问的对象查询该类所有的对象，例如

```bash
有哪些玉米病害
```
然后根据系统给出的列表询问列表中的对象属性，例如

```bash	
玉米叶斑病有什么防治方法
```


演示效果如下所示：

![image-20231113194305159](media\image-20231113194305159.png)

注意：在询问某一对象的属性前必须先让其列出该类别的所有对象
