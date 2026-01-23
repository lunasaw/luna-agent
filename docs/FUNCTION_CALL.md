Function Calling
更新时间：2025-12-30 20:56:13
复制为 MD 格式
产品详情
我的收藏
大模型在面对实时性问题、数学计算等问题时可能效果不佳。Function Calling 通过引入外部工具，让大模型可以回答原本无法解决的问题。

工作原理
Function Calling 通过在应用程序和大模型之间的多步骤交互，使大模型可以参考外部工具信息进行回答。

发起第一次模型调用

应用程序首先向大模型发起一个包含用户问题与模型可调用工具清单的请求。

接收模型的工具调用指令（工具名称与入参）

若模型判断需要调用外部工具，会返回一个JSON格式的指令，用于告知应用程序需要执行的函数与入参。

若模型判断无需调用工具，会返回自然语言格式的回复。
在应用端运行工具

应用程序接收到工具指令后，需要运行工具，获得工具输出结果。

发起第二次模型调用

获取到工具输出结果后，需添加至模型的上下文（messages），再次发起模型调用。

接收来自模型的最终响应

模型将工具输出结果和用户问题信息整合，生成自然语言格式的回复。

工作流程示意图如下所示：

image
支持的模型
通义千问DeepSeekGLMKimi
文本生成模型

通义千问Max

通义千问Plus

通义千问Flash

通义千问Coder

通义千问Turbo

Qwen3

Qwen2.5

Qwen2

Qwen1.5

多模态模型

通义千问VL（仅包括 qwen3-vl-plus、 qwen3-vl-flash系列）

通义千问Omni（仅包括 qwen3-omni-flash 系列）

Qwen3-VL

快速开始
您需要已获取与配置 API Key并配置API Key到环境变量。如果通过 OpenAI SDK 或 DashScope SDK 进行调用，需要安装SDK。

以天气查询场景为例，介绍快速使用 Function Calling 的方法。

OpenAI 兼容DashScope
PythonNode.js

 
from openai import OpenAI
from datetime import datetime
import json
import os
import random


# 初始化客户端
client = OpenAI(
    # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
    # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    # 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
# 模拟用户问题
USER_QUESTION = "北京天气咋样"
# 定义工具列表
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "当你想查询指定城市的天气时非常有用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市或县区，比如北京市、杭州市、余杭区等。",
                    }
                },
                "required": ["location"],
            },
        },
    },
]


# 模拟天气查询工具
def get_current_weather(arguments):
    weather_conditions = ["晴天", "多云", "雨天"]
    random_weather = random.choice(weather_conditions)
    location = arguments["location"]
    return f"{location}今天是{random_weather}。"


# 封装模型响应函数
def get_response(messages):
    completion = client.chat.completions.create(
        model="qwen-plus",
        messages=messages,
        tools=tools,
    )
    return completion


messages = [{"role": "user", "content": USER_QUESTION}]
response = get_response(messages)
assistant_output = response.choices[0].message
if assistant_output.content is None:
    assistant_output.content = ""
messages.append(assistant_output)
# 如果不需要调用工具，直接输出内容
if assistant_output.tool_calls is None:
    print(f"无需调用天气查询工具，直接回复：{assistant_output.content}")
else:
    # 进入工具调用循环
    while assistant_output.tool_calls is not None:
        tool_call = assistant_output.tool_calls[0]
        tool_call_id = tool_call.id
        func_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print(f"正在调用工具 [{func_name}]，参数：{arguments}")
        # 执行工具
        tool_result = get_current_weather(arguments)
        # 构造工具返回信息
        tool_message = {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": tool_result,  # 保持原始工具输出
        }
        print(f"工具返回：{tool_message['content']}")
        messages.append(tool_message)
        # 再次调用模型，获取总结后的自然语言回复
        response = get_response(messages)
        assistant_output = response.choices[0].message
        if assistant_output.content is None:
            assistant_output.content = ""
        messages.append(assistant_output)
    print(f"助手最终回复：{assistant_output.content}")

运行后得到如下输出：

 
正在调用工具 [get_current_weather]，参数：{'location': '北京'}
工具返回：北京今天是多云。
助手最终回复：北京今天是多云的天气。
如何使用
Function Calling 支持两种传入工具信息的方式：

方式一：通过 tools 参数传入（推荐）

请参见如何使用，按照定义工具、创建messages数组、发起 Function Calling、运行工具函数、大模型总结工具函数输出的步骤进行调用。

方式二：通过 System Message 传入

通过 tools 参数传入时，服务端会根据模型自动适配合适的 prompt 模板并组装，因此推荐您优先使用 tools 参数。 如果您在使用 Qwen 模型时不期望使用 tools 参数，请参见通过 System Message 传入工具信息。

以下内容以 OpenAI 兼容调用方式为例，通过 tools 参数传入工具信息，向您分步骤介绍 Function Calling 的详细用法。

假设业务场景中会收到天气查询与时间查询两类问题。

1. 定义工具
工具是连接大模型与外部世界的桥梁，首先需要定义工具。

1.1. 创建工具函数
创建两个工具函数：天气查询工具与时间查询工具。

天气查询工具

接收arguments参数，arguments格式为{"location": "查询的地点"}。工具的输出为字符串，格式为：“{位置}今天是{天气}”。

为了便于演示，此处定义的天气查询工具并不真正查询天气，会从晴天、多云、雨天随机选择。在实际业务中可使用如高德天气查询等工具进行替换。
时间查询工具

时间查询工具不需要输入参数。工具的输出为字符串，格式为：“当前时间：{查询到的时间}。”。

如果使用 Node.js，请运行npm install date-fns安装获取时间的工具包 date-fns：
PythonNode.js

 
## 步骤1:定义工具函数

# 添加导入random模块
import random
from datetime import datetime

# 模拟天气查询工具。返回结果示例：“北京今天是雨天。”
def get_current_weather(arguments):
    # 定义备选的天气条件列表
    weather_conditions = ["晴天", "多云", "雨天"]
    # 随机选择一个天气条件
    random_weather = random.choice(weather_conditions)
    # 从 JSON 中提取位置信息
    location = arguments["location"]
    # 返回格式化的天气信息
    return f"{location}今天是{random_weather}。"

# 查询当前时间的工具。返回结果示例：“当前时间：2024-04-15 17:15:18。“
def get_current_time():
    # 获取当前日期和时间
    current_datetime = datetime.now()
    # 格式化当前日期和时间
    formatted_time = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
    # 返回格式化后的当前时间
    return f"当前时间：{formatted_time}。"

# 测试工具函数并输出结果，运行后续步骤时可以去掉以下四句测试代码
print("测试工具输出：")
print(get_current_weather({"location": "上海"}))
print(get_current_time())
print("\n")

运行工具后，得到输出：

 
测试工具输出：
上海今天是多云。
当前时间：2025-01-08 20:21:45。
1.2 创建 tools 数组
人类在选择工具之前，需要对工具有全面的了解，包括工具的功能、何时使用以及输入参数等。大模型也需要这些信息才能更准确地选择工具。请根据以下 JSON 格式提供工具信息。

type字段固定为"function"；

function字段为 Object 类型；

name字段为自定义的工具函数名称，建议使用与函数相同的名称，如get_current_weather或get_current_time；

description字段是对工具函数功能的描述，大模型会参考该字段来选择是否使用该工具函数。

parameters字段是对工具函数入参的描述，类型是 Object ，大模型会参考该字段来进行入参的提取。如果工具函数不需要输入参数，则无需指定parameters参数。

type字段固定为"object"；

properties字段描述了入参的名称、数据类型与描述，为 Object 类型，Key 值为入参的名称，Value 值为入参的数据类型与描述；

required字段指定哪些参数为必填项，为 Array 类型。

对于天气查询工具来说，工具描述信息的格式如下：

 
{
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": "当你想查询指定城市的天气时非常有用。",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "城市或县区，比如北京市、杭州市、余杭区等。"
                }
            },
            "required": ["location"]
        }
    }
}
在发起 Function Calling 前，需在代码中定义工具信息数组（tools），包含每个工具的函数名、描述和参数定义。这个数组在后续发起Function Calling请求时作为参数传入。

PythonNode.js

 
# 请将以下代码粘贴到步骤1代码后

## 步骤2:创建 tools 数组

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "当你想知道现在的时间时非常有用。",
            "parameters": {}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "当你想查询指定城市的天气时非常有用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市或县区，比如北京市、杭州市、余杭区等。",
                    }
                },
                "required": ["location"]
            }
        }
    }
]
tool_name = [tool["function"]["name"] for tool in tools]
print(f"创建了{len(tools)}个工具，为：{tool_name}\n")

2. 创建messages数组
Function Calling 通过 messages 数组向大模型传入指令与上下文信息。发起 Function Calling 前，messages 数组需要包含 System Message 与 User Message。

System Message
尽管在创建 tools 数组时已经对工具的作用与何时使用工具进行了描述，但在 System Message 中强调何时调用工具通常会提高工具调用的准确率。在当前场景下，可以将 System Prompt 设置为：

 
你是一个很有帮助的助手。如果用户提问关于天气的问题，请调用 ‘get_current_weather’ 函数;
如果用户提问关于时间的问题，请调用‘get_current_time’函数。
请以友好的语气回答问题。
User Message
User Message 用于传入用户提问的问题。假设用户提问“上海天气”，此时的 messages 数组为：

PythonNode.js

 
# 步骤3:创建messages数组
# 请将以下代码粘贴到步骤2 代码后
# 文本生成模型的 User Message示例
messages = [
    {
        "role": "system",
        "content": """你是一个很有帮助的助手。如果用户提问关于天气的问题，请调用 ‘get_current_weather’ 函数;
     如果用户提问关于时间的问题，请调用‘get_current_time’函数。
     请以友好的语气回答问题。""",
    },
    {
        "role": "user",
        "content": "上海天气"
    }
]

# Qwen3-VL模型的 User Message示例
# messages=[
#  {
#         "role": "system",
#         "content": """你是一个很有帮助的助手。如果用户提问关于天气的问题，请调用 ‘get_current_weather’ 函数;
#      如果用户提问关于时间的问题，请调用‘get_current_time’函数。
#      请以友好的语气回答问题。""",
#     },
#     {"role": "user",
#      "content": [{"type": "image_url","image_url": {"url": "https://img.alicdn.com/imgextra/i2/O1CN01FbTJon1ErXVGMRdsN_!!6000000000405-0-tps-1024-683.jpg"}},
#                  {"type": "text", "text": "根据图像上的地点，查询该地点当前天气"}]},
# ]

print("messages 数组创建完成\n") 

由于备选工具包含天气查询与时间查询，也可提问关于当前时间的问题。
3. 发起 Function Calling
将创建好的 tools 与 messages 传入大模型，即可发起一次 Function Calling。大模型会判断是否调用工具。若调用，则返回该工具的函数名与参数。

支持的模型参见支持的模型。
PythonNode.js

 
# 步骤4:发起 function calling
# 请将以下代码粘贴到步骤3 代码后

from openai import OpenAI
import os

client = OpenAI(
    # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
    # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    # 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

def function_calling():
    completion = client.chat.completions.create(
        model="qwen-plus",  # 此处以qwen-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        messages=messages,
        tools=tools
    )
    print("返回对象：")
    print(completion.choices[0].message.model_dump_json())
    print("\n")
    return completion

print("正在发起function calling...")
completion = function_calling()

由于用户提问为上海天气，大模型指定需要使用的工具函数名称为："get_current_weather"，函数的入参为："{\"location\": \"上海\"}"。

 
{
    "content": "",
    "refusal": null,
    "role": "assistant",
    "audio": null,
    "function_call": null,
    "tool_calls": [
        {
            "id": "call_6596dafa2a6a46f7a217da",
            "function": {
                "arguments": "{\"location\": \"上海\"}",
                "name": "get_current_weather"
            },
            "type": "function",
            "index": 0
        }
    ]
}
需要注意，如果问题被大模型判断为无需使用工具，会通过content参数直接回复。在输入“你好”时，tool_calls参数为空，返回对象格式为：

 
{
    "content": "你好！有什么可以帮助你的吗？如果你有关于天气或者时间的问题，我特别擅长回答。",
    "refusal": null,
    "role": "assistant",
    "audio": null,
    "function_call": null,
    "tool_calls": null
}
如果tool_calls 参数为空，可使程序直接返回 content，无需运行以下步骤。
若希望每次发起 Function Calling 后大模型都可以选择指定工具，请参见强制工具调用。
4. 运行工具函数
运行工具函数是将大模型的决策转化为实际操作的关键步骤。

运行工具函数的过程由您的计算环境而非大模型来完成。
由于大模型只可以输出字符串格式的内容，因此在运行工具函数前，需要对字符串格式的工具函数与入参分别解析。

工具函数

建立一个工具函数名称到工具函数实体的映射function_mapper，将返回的工具函数字符串映射到工具函数实体；

入参

Function Calling 返回的入参为 JSON 字符串，使用工具将其解析为 JSON 对象，提取入参信息。

完成解析后，将参数传入工具函数并执行，获取输出结果。

PythonNode.js

 
# 步骤5:运行工具函数
# 请将以下代码粘贴到步骤4 代码后
import json

print("正在执行工具函数...")
# 从返回的结果中获取函数名称和入参
function_name = completion.choices[0].message.tool_calls[0].function.name
arguments_string = completion.choices[0].message.tool_calls[0].function.arguments

# 使用json模块解析参数字符串
arguments = json.loads(arguments_string)
# 创建一个函数映射表
function_mapper = {
    "get_current_weather": get_current_weather,
    "get_current_time": get_current_time
}
# 获取函数实体
function = function_mapper[function_name]
# 如果入参为空，则直接调用函数
if arguments == {}:
    function_output = function()
# 否则，传入参数后调用函数
else:
    function_output = function(arguments)
# 打印工具的输出
print(f"工具函数输出：{function_output}\n")

运行后得到如下输出：

 
上海今天是多云。
说明
在实际业务场景中，许多工具的核心功能是执行具体操作（如邮件发送、文件上传等），而非数据查询，这类工具执行后不会输出字符串。为帮助大模型了解工具运行状态，建议在设计此类工具时添加如“邮件发送完成”、"操作执行失败"等状态描述信息。

5. 大模型总结工具函数输出
工具函数的输出格式较为固定，如果直接返回给用户，可能会有语气生硬、不够灵活等问题。如果您希望大模型能够综合用户输入以及工具输出结果，生成自然语言风格的回复，可以将工具输出提交到模型上下文并再次向模型发出请求。

添加 Assistant Message

发起 Function Calling后，通过completion.choices[0].message得到 Assistant Message，首先将它添加到 messages 数组中；

添加 Tool Message

将工具的输出通过{"role": "tool", "content": "工具的输出","tool_call_id": completion.choices[0].message.tool_calls[0].id}形式添加到 messages 数组。

说明
请确保工具的输出为字符串格式。

tool_call_id 是系统为每一次的工具调用请求生成的唯一标识符。模型可能一次性要求调用多个工具，将多个工具结果返回给模型时，tool_call_id可确保工具的输出结果能够与它的调用意图对应。

PythonNode.js

 
# 步骤6:向大模型提交工具输出
# 请将以下代码粘贴到步骤5 代码后

messages.append(completion.choices[0].message)
print("已添加assistant message")
messages.append({"role": "tool", "content": function_output, "tool_call_id": completion.choices[0].message.tool_calls[0].id})
print("已添加tool message\n")

此时的 messages 数组为：

 
[
  System Message -- 指引模型调用工具的策略
  User Message -- 用户的问题
  Assistant Message -- 模型返回的工具调用信息
  Tool Message -- 工具的输出信息（如果采用下文介绍的并行工具调用，可能有多个 Tool Message）
]
更新 messages 数组后，运行以下代码。

PythonNode.js

 
# 步骤7:大模型总结工具输出
# 请将以下代码粘贴到步骤6 代码后
print("正在总结工具输出...")
completion = function_calling()

可从content得到回复内容：“上海今天的天气是多云。如果您有其他问题，欢迎继续提问。”

 
{
    "content": "上海今天的天气是多云。如果您有其他问题，欢迎继续提问。",
    "refusal": null,
    "role": "assistant",
    "audio": null,
    "function_call": null,
    "tool_calls": null
}
至此，您已完成了一次完整的 Function Calling 流程。

进阶用法
指定工具调用方式
并行工具调用
单一城市的天气查询经过一次工具调用即可。如果输入问题需要调用多次工具，如“北京上海的天气如何”或“杭州天气，以及现在几点了”，发起 Function Calling 后只会返回一个工具调用信息，以提问“北京上海的天气如何”为例：

 
{
    "content": "",
    "refusal": null,
    "role": "assistant",
    "audio": null,
    "function_call": null,
    "tool_calls": [
        {
            "id": "call_61a2bbd82a8042289f1ff2",
            "function": {
                "arguments": "{\"location\": \"北京市\"}",
                "name": "get_current_weather"
            },
            "type": "function",
            "index": 0
        }
    ]
}
返回结果中只有北京市的入参信息。为了解决这一问题，在发起 Function Calling时，可设置请求参数parallel_tool_calls为true，这样返回对象中将包含所有需要调用的工具函数与入参信息。

说明
并行工具调用适合任务之间无依赖的情况。若任务之间有依赖关系（工具A的输入与工具B的输出结果有关），请参见快速开始，通过while循环实现串行工具调用（一次调用一个工具）。

PythonNode.js

 
def function_calling():
    completion = client.chat.completions.create(
        model="qwen-plus",  # 此处以 qwen-plus 为例，可按需更换模型名称
        messages=messages,
        tools=tools,
        # 新增参数
        parallel_tool_calls=True
    )
    print("返回对象：")
    print(completion.choices[0].message.model_dump_json())
    print("\n")
    return completion

print("正在发起function calling...")
completion = function_calling()

在返回对象的tool_calls数组中包含了北京上海的入参信息：

 
{
    "content": "",
    "role": "assistant",
    "tool_calls": [
        {
            "function": {
                "name": "get_current_weather",
                "arguments": "{\"location\": \"北京市\"}"
            },
            "index": 0,
            "id": "call_c2d8a3a24c4d4929b26ae2",
            "type": "function"
        },
        {
            "function": {
                "name": "get_current_weather",
                "arguments": "{\"location\": \"上海市\"}"
            },
            "index": 1,
            "id": "call_dc7f2f678f1944da9194cd",
            "type": "function"
        }
    ]
}
强制工具调用
大模型生成内容具有不确定性，有时会选择错误的工具进行调用。如果您希望对于某一类问题，大模型能够采取人为设定的策略（如强制使用某个工具、强制不使用工具），可修改tool_choice参数。tool_choice参数的默认值为"auto"，表示由大模型自主判断如何进行工具调用。

大模型总结工具函数输出时，请将tool_choice参数去除，否则 API 仍会返回工具调用信息。
强制使用某个工具

如果您希望对于某一类问题，Function Calling 能强制调用某个工具，可设定tool_choice参数为{"type": "function", "function": {"name": "the_function_to_call"}}，大模型将不参与工具的选择，只输出入参信息。

假设当前场景中只包含天气查询的问题，可修改 function_calling 代码为：

PythonNode.js

 
def function_calling():
    completion = client.chat.completions.create(
        model="qwen-plus",
        messages=messages,
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "get_current_weather"}}
    )
    print(completion.model_dump_json())

function_calling()

无论输入什么问题，返回对象的工具函数都会是get_current_weather。

使用该策略前请确保问题与选择的工具相关，否则可能返回不符合预期的结果。
强制不使用工具

如果您希望无论输入什么问题，Function Calling 都不会进行工具调用（返回对象中包含回复内容content而tool_calls参数为空），可设定tool_choice参数为"none"，或不传入tools参数，Function Calling 返回的tool_calls参数将始终为空。

假设当前场景中的问题均无需调用工具，可修改 function_calling 代码为：

PythonNode.js

 
def function_calling():
    completion = client.chat.completions.create(
        model="qwen-plus",
        messages=messages,
        tools=tools,
        tool_choice="none"
    )
    print(completion.model_dump_json())

function_calling()

多轮对话
用户可能在第一轮提问“北京天气”，第二轮提问“上海的呢？”若模型上下文中没有第一轮的信息，模型无法判断需要调用哪个工具。建议在多轮对话场景中，每轮结束后维持 messages 数组，在此基础上添加 User Message并发起 Function Calling以及后续步骤。messages 结构如下所示：

 
[
  System Message -- 指引模型调用工具的策略
  User Message -- 用户的问题
  Assistant Message -- 模型返回的工具调用信息
  Tool Message -- 工具的输出信息
  Assistant Message -- 模型总结的工具调用信息
  User Message -- 用户第二轮的问题
]
流式输出
为了提升用户体验和减少等待时间，可使用流式输出实时获取工具函数名称与入参信息。其中：

工具调用的参数信息：以数据流的形式分块返回。

工具函数名称：在流式响应的第一个数据块中返回。

PythonNode.js

 
from openai import OpenAI
import os

client = OpenAI(
    # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
    # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    # 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "当你想查询指定城市的天气时非常有用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市或县区，比如北京市、杭州市、余杭区等。",
                    }
                },
                "required": ["location"],
            },
        },
    },
]

stream = client.chat.completions.create(
    model="qwen-plus",
    messages=[{"role": "user", "content": "杭州天气?"}],
    tools=tools,
    stream=True
)

for chunk in stream:
    delta = chunk.choices[0].delta
    print(delta.tool_calls)

运行后得到如下输出：

 
[ChoiceDeltaToolCall(index=0, id='call_8f08d2b0fc0c4d8fab7123', function=ChoiceDeltaToolCallFunction(arguments='{"location":', name='get_current_weather'), type='function')]
[ChoiceDeltaToolCall(index=0, id='', function=ChoiceDeltaToolCallFunction(arguments=' "杭州"}', name=None), type='function')]
None
运行以下代码拼接入参信息（arguments）：

PythonNode.js

 
tool_calls = {}
for response_chunk in stream:
    delta_tool_calls = response_chunk.choices[0].delta.tool_calls
    if delta_tool_calls:
        for tool_call_chunk in delta_tool_calls:
            call_index = tool_call_chunk.index
            tool_call_chunk.function.arguments = tool_call_chunk.function.arguments or ""
            if call_index not in tool_calls:
                tool_calls[call_index] = tool_call_chunk
            else:
                tool_calls[call_index].function.arguments += tool_call_chunk.function.arguments
print(tool_calls[0].model_dump_json())

获得如下输出：

 
{"index":0,"id":"call_16c72bef988a4c6c8cc662","function":{"arguments":"{\"location\": \"杭州\"}","name":"get_current_weather"},"type":"function"}
在使用大模型总结工具函数输出步骤，添加的 Assistant Message 需要符合下方格式。仅需将下方的tool_calls中的元素替换为以上内容即可。

 
{
    "content": "",
    "refusal": None,
    "role": "assistant",
    "audio": None,
    "function_call": None,
    "tool_calls": [
        {
            "id": "call_xxx",
            "function": {
                "arguments": '{"location": "xx"}',
                "name": "get_current_weather",
            },
            "type": "function",
            "index": 0,
        }
    ],
}
Qwen3-Omni-Flash模型的工具调用
在获取工具信息阶段，Qwen3-Omni-Flash模型的使用方式与其他模型有以下不同：

必须使用流式输出：Qwen3-Omni-Flash仅支持流式输出，在获取工具信息时也必须设置 stream=True。

建议仅输出文本：模型在获取工具信息（函数的名称和参数）时仅需文本信息，为避免生成不必要的音频，建议设置 modalities=["text"]。当输出包含文本和音频两种模态时，获取工具信息时需要跳过音频数据块。

Qwen3-Omni-Flash详情参见：全模态。
PythonNode.js

 
from openai import OpenAI
import os

client = OpenAI(
    # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
    # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    # 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "当你想查询指定城市的天气时非常有用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市或县区，比如北京市、杭州市、余杭区等。",
                    }
                },
                "required": ["location"],
            },
        },
    },
]

completion = client.chat.completions.create(
    model="qwen3-omni-flash",
    messages=[{"role": "user", "content": "杭州天气?"}],

    # 设置输出数据的模态，可取值：["text"]、["text","audio"]，建议设置为["text"]
    modalities=["text"],
    
    # stream 必须设置为 True，否则会报错
    stream=True,
    tools=tools
)

for chunk in completion:
    # 如果输出包含音频模态，请将下列条件改为：if chunk.choices and not hasattr(chunk.choices[0].delta, "audio"): 
    if chunk.choices:
        delta = chunk.choices[0].delta
        print(delta.tool_calls)

运行后得到如下输出：

 
[ChoiceDeltaToolCall(index=0, id='call_391c8e5787bc4972a388aa', function=ChoiceDeltaToolCallFunction(arguments=None, name='get_current_weather'), type='function')]
[ChoiceDeltaToolCall(index=0, id='call_391c8e5787bc4972a388aa', function=ChoiceDeltaToolCallFunction(arguments=' {"location": "杭州市"}', name=None), type='function')]
None
拼接入参信息（arguments）的代码请参见流式输出。

深度思考模型的工具调用
深度思考模型在输出工具调用信息前会进行思考，可以提升决策的可解释性与可靠性。

思考过程

模型逐步分析用户意图、识别所需工具、验证参数合法性，并规划调用策略；

工具调用

模型以结构化格式输出一个或多个函数调用请求。

支持并行工具调用。
以下展示流式调用深度思考模型的工具调用示例。

文本生成思考模型请参见：深度思考；多模态思考模型请参见：视觉理解、全模态。
tool_choice参数只支持设置为"auto"（默认值，表示由模型自主选择工具）或"none"（强制模型不选择工具）。
OpenAI兼容DashScope
PythonNode.jsHTTP
示例代码
 
import os
from openai import OpenAI

# 初始化OpenAI客户端，配置阿里云DashScope服务
client = OpenAI(
    # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
    # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
    api_key=os.getenv("DASHSCOPE_API_KEY"),  # 从环境变量读取API密钥
    # 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# 定义可用工具列表
tools = [
    # 工具1 获取当前时刻的时间
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "当你想知道现在的时间时非常有用。",
            "parameters": {}  # 无需参数
        }
    },  
    # 工具2 获取指定城市的天气
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "当你想查询指定城市的天气时非常有用。",
            "parameters": {  
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市或县区，比如北京市、杭州市、余杭区等。"
                    }
                },
                "required": ["location"]  # 必填参数
            }
        }
    }
]

messages = [{"role": "user", "content": input("请输入问题：")}]

# Qwen3-VL模型的 message示例
# messages = [{
#     "role": "user",
#     "content": [
#              {"type": "image_url","image_url": {"url": "https://img.alicdn.com/imgextra/i4/O1CN014CJhzi20NOzo7atOC_!!6000000006837-2-tps-2048-1365.png"}},
#              {"type": "text", "text": "根据图像上的地点，请问该地点当前的天气"}]
#     }]

completion = client.chat.completions.create(
    # 此处以qwen-plus为例，可更换为其它深度思考模型
    model="qwen-plus",
    messages=messages,
    extra_body={
        # 开启深度思考
        "enable_thinking": True
    },
    tools=tools,
    parallel_tool_calls=True,
    stream=True,
    # 解除注释后，可以获取到token消耗信息
    # stream_options={
    #     "include_usage": True
    # }
)

reasoning_content = ""  # 定义完整思考过程
answer_content = ""     # 定义完整回复
tool_info = []          # 存储工具调用信息
is_answering = False   # 判断是否结束思考过程并开始回复
print("="*20+"思考过程"+"="*20)
for chunk in completion:
    if not chunk.choices:
        # 处理用量统计信息
        print("\n"+"="*20+"Usage"+"="*20)
        print(chunk.usage)
    else:
        delta = chunk.choices[0].delta
        # 处理AI的思考过程（链式推理）
        if hasattr(delta, 'reasoning_content') and delta.reasoning_content is not None:
            reasoning_content += delta.reasoning_content
            print(delta.reasoning_content,end="",flush=True)  # 实时输出思考过程
            
        # 处理最终回复内容
        else:
            if not is_answering:  # 首次进入回复阶段时打印标题
                is_answering = True
                print("\n"+"="*20+"回复内容"+"="*20)
            if delta.content is not None:
                answer_content += delta.content
                print(delta.content,end="",flush=True)  # 流式输出回复内容
            
            # 处理工具调用信息（支持并行工具调用）
            if delta.tool_calls is not None:
                for tool_call in delta.tool_calls:
                    index = tool_call.index  # 工具调用索引，用于并行调用
                    
                    # 动态扩展工具信息存储列表
                    while len(tool_info) <= index:
                        tool_info.append({})
                    
                    # 收集工具调用ID（用于后续函数调用）
                    if tool_call.id:
                        tool_info[index]['id'] = tool_info[index].get('id', '') + tool_call.id
                    
                    # 收集函数名称（用于后续路由到具体函数）
                    if tool_call.function and tool_call.function.name:
                        tool_info[index]['name'] = tool_info[index].get('name', '') + tool_call.function.name
                    
                    # 收集函数参数（JSON字符串格式，需要后续解析）
                    if tool_call.function and tool_call.function.arguments:
                        tool_info[index]['arguments'] = tool_info[index].get('arguments', '') + tool_call.function.arguments
            
print(f"\n"+"="*19+"工具调用信息"+"="*19)
if not tool_info:
    print("没有工具调用")
else:
    print(tool_info)
返回结果
输入“四个直辖市的天气”，得到以下返回结果：

 
====================思考过程====================
好的，用户问的是“四个直辖市的天气”。首先，我需要明确四个直辖市是哪几个。根据中国的行政区划，直辖市包括北京、上海、天津和重庆。所以用户想知道这四个城市的天气情况。

接下来，我需要检查可用的工具。提供的工具中有get_current_weather函数，参数是location，类型字符串。每个城市需要单独查询，因为函数一次只能查一个地点。因此，我需要为每个直辖市调用一次这个函数。

然后，我需要考虑如何生成正确的工具调用。每个调用应该包含城市名称作为参数。比如，第一个调用是北京，第二个是上海，依此类推。确保参数名称是location，值是正确的城市名。

另外，用户可能希望得到每个城市的天气信息，所以需要确保每个函数调用都正确无误。可能需要连续调用四次，每次对应一个城市。不过，根据工具的使用规则，可能需要分多次处理，或者一次生成多个调用。但根据示例，可能每次只调用一个函数，所以可能需要逐步进行。

最后，确认是否有其他需要考虑的因素，比如参数是否正确，城市名称是否准确，以及是否需要处理可能的错误情况，比如城市不存在或API不可用。但目前看来，四个直辖市都是明确的，应该没问题。
====================回复内容====================

===================工具调用信息===================
[{'id': 'call_767af2834c12488a8fe6e3', 'name': 'get_current_weather', 'arguments': '{"location": "北京市"}'}, {'id': 'call_2cb05a349c89437a947ada', 'name': 'get_current_weather', 'arguments': '{"location": "上海市"}'}, {'id': 'call_988dd180b2ca4b0a864ea7', 'name': 'get_current_weather', 'arguments': '{"location": "天津市"}'}, {'id': 'call_4e98c57ea96a40dba26d12', 'name': 'get_current_weather', 'arguments': '{"location": "重庆市"}'}]
应用于生产环境
测试工具调用准确率
建立评估体系：

构建贴近真实业务的测试数据集，并定义清晰的评估指标，如：工具选择准确率、参数提取准确率、端到端成功率等。

优化提示词

根据测试暴露出的具体问题（选错工具、参数错误），针对性地优化系统提示词、工具描述和参数描述，是核心的调优手段。

升级模型

当提示词工程调优无法提升性能时，升级到能力更强的模型版本（如 qwen3-max-preview）是提升指标最直接有效的方法。

动态控制工具数量
当应用集成的工具数量超过几十甚至上百个时，将整个工具库全部提供给模型会带来以下问题：

性能下降：模型在庞大的工具集中选择正确工具的难度剧增；

成本与延迟：大量的工具描述会消耗巨量的输入 Token，导致费用上升和响应变慢；

解决方案是在调用模型前，增加一个工具路由/检索层，根据用户当前查询，从完整的工具库中快速、精准地筛选出一个小而相关的工具子集，再将其提供给模型。

实现工具路由的几种主流方法：

语义检索

预先将所有工具的描述信息（description）通过 Embedding 模型转化为向量，并存入向量数据库。当用户查询时，将查询向量通过向量相似度搜索，召回最相关的 Top-K 个工具。

混合检索

将语义检索的“模糊匹配”能力与传统关键词或元数据标签的“精确匹配”能力相结合。为工具添加 tags 或 keywords 字段，检索时同时进行向量搜索和关键词过滤，可以大幅提升高频或特定场景下的召回精准度。

轻量级 LLM 路由器

对于更复杂的路由逻辑，可以使用一个更小、更快、更便宜的模型（如 Qwen-Flash）作为前置“路由模型”。它的任务是根据用户问题输出相关的工具名称列表。

实践建议

保持候选集精简：无论使用何种方法，最终提供给主模型的工具数量建议不超过 20 个。这是在模型认知负荷、成本、延迟和准确率之间的最佳平衡点。

分层过滤策略：可以构建一个漏斗式的路由策略。例如，先用成本极低的关键词/规则匹配进行第一轮筛选，过滤掉明显不相关的工具，再对剩余的工具进行语义检索，从而提高效率和质量。

工具安全性原则
将工具执行能力开放给大模型时，必须将安全置于首位。核心原则是“最小权限”和“人类确认”。

最小权限原则：为模型提供的工具集应严格遵守最小权限原则。默认情况下，工具应是只读的（如查询天气、搜索文档），避免直接提供任何涉及状态变更或资源操作的“写”权限。

危险工具隔离：请勿向大模型直接提供危险工具，例如执行任意代码（code interpreter）、操作文件系统（fs.delete）、执行数据库删除或更新操作（db.drop_table）或涉及资金流转的工具（payment.transfer）。

人类参与：对于所有高权限或不可逆的操作，必须引入人工审核和确认环节。模型可以生成操作请求，但最终的执行“按钮”必须由人类用户点击。例如，模型可以准备好一封邮件，但发送操作需要用户确认。

用户体验优化
Function Calling 链路较长，任何一个环节出问题都可能导致用户体验下降。

处理工具运行失败
工具运行失败是常见情况。可采取以下策略：

最大重试次数：设置合理的重试上限（例如 3 次），避免因连续失败导致用户长时间等待或系统资源浪费。

提供兜底话术：当重试耗尽或遇到无法解决的错误时，应向用户返回清晰、友好的提示信息，例如：“抱歉，我暂时无法查询到相关信息，可能是服务有些繁忙，请您稍后再试。”

应对处理延迟
较高的延迟会降低用户满意度，需要通过前端交互和后端优化来改善。

设置超时时间：为 Function Calling 的每一步设置独立且合理的超时时间。一旦超时，应立即中断操作并给出反馈。

提供即时反馈：开始执行 Function Calling 时，建议在界面上给出提示，如“正在为您查询天气...”、“正在搜索相关信息...”，向用户实时反馈处理进度。

