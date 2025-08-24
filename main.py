#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流程图转换系统 - 大数据比赛版本
使用讯飞Qwen2.5-VL API将PNG流程图转换为Mermaid代码
"""

import os
import base64
import json
import requests
from pathlib import Path
import time
from typing import Dict, List, Optional

# 配置信息
API_BASE_URL = "https://maas-api.cn-huabei-1.xf-yun.com/v1"
API_KEY = "sk-iBuVfdtBDgb27dhAE25f548fD77a47B086D94dFdBc8a775c"
MODEL_NAME = "qwen2.5-vl-72b-instruct"  # 使用讯飞提供的Qwen2.5-VL模型

# 目录配置
TEST_IMAGE_DIR = "测试集/image"
OUTPUT_DIR = "submit"

class FlowchartConverter:
    """流程图转换器"""
    
    def __init__(self):
        self.api_url = f"{API_BASE_URL}/chat/completions"
        self.models_url = f"{API_BASE_URL}/models"
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        try:
            response = requests.get(self.models_url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if 'data' in result:
                    models = [model['id'] for model in result['data']]
                    return models
            print(f"获取模型列表失败: {response.status_code}, {response.text}")
            return []
        except Exception as e:
            print(f"获取模型列表异常: {str(e)}")
            return []
        
    def encode_image_to_base64(self, image_path: str) -> str:
        """将图片编码为base64格式，包含格式验证和优化"""
        try:
            # 检查文件是否存在
            if not os.path.exists(image_path):
                print(f"图片文件不存在: {image_path}")
                return ""
            
            # 检查文件大小（限制为10MB）
            file_size = os.path.getsize(image_path)
            if file_size > 10 * 1024 * 1024:
                print(f"图片文件过大: {file_size / 1024 / 1024:.2f}MB，超过10MB限制")
                return ""
            
            # 验证图片格式
            valid_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
            file_ext = os.path.splitext(image_path)[1].lower()
            if file_ext not in valid_extensions:
                print(f"不支持的图片格式: {file_ext}")
                return ""
            
            print(f"正在编码图片: {image_path} (大小: {file_size / 1024:.2f}KB)")
            
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                encoded = base64.b64encode(image_data).decode('utf-8')
                print(f"图片编码成功，base64长度: {len(encoded)}")
                return encoded
                
        except Exception as e:
            print(f"图片编码失败: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def create_prompt(self) -> str:
        """创建用于流程图识别的提示词"""
        return """
你是一个专业的流程图分析专家。请仔细观察这张流程图图片，并将其准确转换为Mermaid flowchart代码。

分析步骤：
1. 仔细识别图片中的每个节点：
   - 矩形框：用 [文本] 表示
   - 菱形（判断节点）：用 {文本} 表示  
   - 圆形/椭圆：用 ((文本)) 表示
   - 圆角矩形：用 (文本) 表示

2. 识别连接关系：
   - 观察箭头方向和连接线
   - 注意分支和汇合点
   - 识别连接线上的标签文字

3. 确定布局方向：
   - 如果是从上到下：使用 flowchart TD
   - 如果是从左到右：使用 flowchart LR

输出要求：
- 必须以 ```mermaid 开始，以 ``` 结束
- 节点ID使用简单字母：A, B, C, D...
- 保持原图的逻辑流程和文本内容
- 判断节点的分支用 |条件| 标注
- 确保语法完全正确

示例格式：
```mermaid
flowchart TD
    A[开始] --> B[处理数据]
    B --> C{是否成功?}
    C -->|是| D[保存结果]
    C -->|否| E[错误处理]
    D --> F[结束]
    E --> F
```

重要提醒：
- 只输出mermaid代码块，不要添加任何解释
- 确保所有节点都有连接关系
- 文本内容要与图片中的文字完全一致
- 语法必须严格遵循Mermaid标准
"""
    
    def call_api(self, image_base64: str, max_retries: int = 3) -> Optional[str]:
        """调用讯飞API进行图像理解，带重试机制"""
        for attempt in range(max_retries):
            try:
                payload = {
                    "model": MODEL_NAME,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": self.create_prompt()
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.1
                }
                
                # 详细日志：请求信息
                print(f"\n=== API调用详情 (尝试 {attempt + 1}/{max_retries}) ===")
                print(f"请求URL: {self.api_url}")
                print(f"使用模型: {MODEL_NAME}")
                print(f"请求头: {self.headers}")
                print(f"图片base64长度: {len(image_base64)} 字符")
                print(f"提示词长度: {len(self.create_prompt())} 字符")
                
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=90  # 增加超时时间
                )
                
                # 详细日志：响应信息
                print(f"响应状态码: {response.status_code}")
                print(f"响应头: {dict(response.headers)}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"响应JSON结构: {list(result.keys()) if isinstance(result, dict) else type(result)}")
                    
                    if 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content']
                        print(f"API返回内容长度: {len(content)} 字符")
                        print(f"API返回内容预览: {content[:200]}...")
                        extracted_code = self.extract_mermaid_code(content)
                        print(f"提取的Mermaid代码: {extracted_code[:100]}...")
                        return extracted_code
                    else:
                        print(f"API响应格式错误，完整响应: {result}")
                        return None
                else:
                    error_msg = response.text
                    print(f"API调用失败详情:")
                    print(f"  状态码: {response.status_code}")
                    print(f"  错误信息: {error_msg}")
                    print(f"  响应头: {dict(response.headers)}")
                    
                    # 如果是内容审核问题，不重试
                    if "法律 法规" in error_msg or "10040" in error_msg:
                        print("内容审核失败，跳过重试")
                        return None
                    
                    # 其他错误，等待后重试
                    if attempt < max_retries - 1:
                        print(f"第{attempt + 1}次尝试失败，等待5秒后重试...")
                        time.sleep(5)
                        continue
                    return None
                    
            except Exception as e:
                print(f"API调用异常详情:")
                print(f"  异常类型: {type(e).__name__}")
                print(f"  异常信息: {str(e)}")
                import traceback
                print(f"  异常堆栈: {traceback.format_exc()}")
                
                if attempt < max_retries - 1:
                    print(f"第{attempt + 1}次尝试异常，等待5秒后重试...")
                    time.sleep(5)
                    continue
                return None
        
        return None
    
    def extract_mermaid_code(self, content: str) -> str:
        """从API响应中提取Mermaid代码"""
        try:
            print(f"\n=== 开始提取Mermaid代码 ===")
            print(f"原始内容长度: {len(content)} 字符")
            print(f"原始内容前500字符: {content[:500]}")
            
            # 首先修正常见的拼写错误
            import re
            corrected_content = content
            corrected_content = re.sub(r'```\s*mermind', '```mermaid', corrected_content, flags=re.IGNORECASE)
            corrected_content = re.sub(r'```\s*mermai\s*d', '```mermaid', corrected_content, flags=re.IGNORECASE)
            corrected_content = re.sub(r'flowchatr\b', 'flowchart', corrected_content, flags=re.IGNORECASE)
            corrected_content = re.sub(r'flowchat\s*t', 'flowchart', corrected_content, flags=re.IGNORECASE)
            
            print(f"修正拼写错误后的内容前500字符: {corrected_content[:500]}")
            
            # 查找```mermaid和```之间的内容
            pattern = r'```mermaid\s*\n([\s\S]*?)\n```'
            matches = re.findall(pattern, corrected_content, re.IGNORECASE)
            
            print(f"标准格式匹配结果: {len(matches)} 个")
            
            if matches:
                # 取第一个匹配的代码块
                mermaid_code = matches[0].strip()
                print(f"提取到的原始代码: {mermaid_code}")
                
                # 进一步清理可能的拼写错误
                mermaid_code = re.sub(r'flowchatr\b', 'flowchart', mermaid_code, flags=re.IGNORECASE)
                mermaid_code = re.sub(r'flowchat\s*t', 'flowchart', mermaid_code, flags=re.IGNORECASE)
                
                print(f"清理后的代码: {mermaid_code}")
                return mermaid_code
            else:
                print("未找到标准格式，尝试查找flowchart开头的内容")
                
                # 如果没找到标准格式，尝试查找flowchart开头的内容
                lines = content.split('\n')
                mermaid_lines = []
                in_mermaid = False
                
                for i, line in enumerate(lines):
                    # 修正可能的拼写错误
                    line_corrected = re.sub(r'flowchat\s*t', 'flowchart', line, flags=re.IGNORECASE)
                    
                    if 'flowchart' in line_corrected.lower():
                        print(f"找到flowchart开始行 {i}: {line_corrected}")
                        in_mermaid = True
                        mermaid_lines.append(line_corrected.strip())
                    elif in_mermaid and line.strip():
                        if line.strip().startswith('```'):
                            print(f"遇到结束标记，停止提取")
                            break
                        mermaid_lines.append(line.strip())
                        print(f"添加行 {i}: {line.strip()}")
                    elif in_mermaid and not line.strip():
                        continue
                
                if mermaid_lines:
                    result = '\n'.join(mermaid_lines)
                    print(f"通过flowchart提取的代码: {result}")
                    return result
                
                # 尝试更宽松的匹配
                print("尝试更宽松的匹配...")
                flowchart_pattern = r'(flowchart\s+\w+[\s\S]*?)(?=\n\n|$|```)'  
                flowchart_matches = re.findall(flowchart_pattern, content, re.IGNORECASE)
                
                if flowchart_matches:
                    result = flowchart_matches[0].strip()
                    print(f"宽松匹配提取的代码: {result}")
                    return result
                
                print("所有提取方法都失败，返回默认代码")
                # 如果还是没找到，返回默认代码
                return "flowchart TD\n    A[开始] --> B[结束]"
                
        except Exception as e:
            print(f"提取Mermaid代码时出错: {str(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            return "flowchart TD\n    A[开始] --> B[结束]"
    
    def process_single_image(self, image_path: str) -> Optional[str]:
        """处理单张图片"""
        try:
            print(f"正在处理: {image_path}")
            
            # 编码图片
            image_base64 = self.encode_image_to_base64(image_path)
            
            # 调用API
            mermaid_code = self.call_api(image_base64)
            
            if mermaid_code:
                if "flowchart TD\n    A[开始] --> B[结束]" not in mermaid_code:
                    print(f"✓ 成功生成Mermaid代码")
                    return mermaid_code
                else:
                    print(f"✗ 提取的代码为空或为默认代码")
                    return None
            else:
                print(f"✗ 生成失败")
                return None
                
        except Exception as e:
            print(f"处理图片失败: {str(e)}")
            return None
    
    def save_result(self, filename: str, mermaid_code: str):
        """保存结果到markdown文件"""
        # 确保输出目录存在
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 生成输出文件路径
        output_path = os.path.join(OUTPUT_DIR, f"{filename}.md")
        
        # 格式化输出内容
        content = f"```mermaid\n{mermaid_code}\n```\n"
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"结果已保存到: {output_path}")
    
    def process_all_images(self):
        """批量处理所有测试图片"""
        if not os.path.exists(TEST_IMAGE_DIR):
            print(f"错误: 测试图片目录不存在: {TEST_IMAGE_DIR}")
            return
        
        # 获取所有PNG图片
        image_files = [f for f in os.listdir(TEST_IMAGE_DIR) if f.endswith('.png')]
        
        if not image_files:
            print(f"错误: 在 {TEST_IMAGE_DIR} 中没有找到PNG图片")
            return
        
        print(f"找到 {len(image_files)} 张图片，开始批量处理...")
        
        success_count = 0
        failed_count = 0
        content_blocked_count = 0
        
        for i, image_file in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] 处理: {image_file}")
            
            image_path = os.path.join(TEST_IMAGE_DIR, image_file)
            filename = os.path.splitext(image_file)[0]  # 去掉.png扩展名
            
            # 处理图片
            mermaid_code = self.process_single_image(image_path)
            
            # 保存结果
            if mermaid_code:
                self.save_result(filename, mermaid_code)
            else:
                default_code = "flowchart TD\n    A[开始] --> B[结束]"
                self.save_result(filename, default_code)
            
            # 统计结果
            if mermaid_code and "flowchart TD\n    A[开始] --> B[结束]" not in mermaid_code:
                success_count += 1
                print("✓ 成功生成Mermaid代码")
            elif "内容审核失败" in str(mermaid_code) if mermaid_code else False:
                content_blocked_count += 1
                failed_count += 1
                print("✗ 内容审核失败")
            else:
                failed_count += 1
                print("✗ 生成失败，使用默认代码")
            
            # 显示进度统计
            if i % 10 == 0 or i == len(image_files):
                success_rate = (success_count / i) * 100
                print(f"\n--- 进度统计 [{i}/{len(image_files)}] ---")
                print(f"成功: {success_count}, 失败: {failed_count}, 内容审核: {content_blocked_count}")
                print(f"成功率: {success_rate:.1f}%\n")
            
            # 添加延迟避免API限流
            if i < len(image_files):
                time.sleep(1)
        
        print(f"\n批量处理完成!")
        print(f"成功: {success_count} 张")
        print(f"失败: {failed_count} 张")
        print(f"结果保存在: {OUTPUT_DIR} 目录")

def main():
    """主函数"""
    print("=" * 50)
    print("流程图转换系统 - 大数据比赛版本")
    print("=" * 50)
    
    # 创建转换器实例
    converter = FlowchartConverter()
    
    # 查询可用模型
    print("正在查询可用模型...")
    available_models = converter.get_available_models()
    if available_models:
        print(f"可用模型: {available_models}")
        
        # 优先级顺序的视觉模型列表
        preferred_models = [
            "qwen2.5-vl-72b-instruct",
            "qwen2.5-vl-32b-instruct", 
            "qwen2.5-vl-7b-instruct",
            "qwen-vl-max",
            "qwen-vl-plus",
            "qwen-vl-chat"
        ]
        
        # 寻找最佳匹配的模型
        selected_model = None
        for preferred in preferred_models:
            if preferred in available_models:
                selected_model = preferred
                break
        
        # 如果没找到优先模型，寻找包含vision或vl的模型
        if not selected_model:
            vision_models = [m for m in available_models if 'vl' in m.lower() or 'vision' in m.lower()]
            if vision_models:
                selected_model = vision_models[0]
        
        if selected_model:
            global MODEL_NAME
            MODEL_NAME = selected_model
            print(f"✓ 选择模型: {MODEL_NAME}")
        else:
            print(f"⚠ 警告: 未找到合适的视觉模型，使用默认模型: {MODEL_NAME}")
    else:
        print(f"⚠ 警告: 无法获取模型列表，使用默认模型: {MODEL_NAME}")
    
    print(f"当前使用模型: {MODEL_NAME}")
    print()
    
    # 批量处理所有图片
    converter.process_all_images()
    
    print("\n程序执行完成!")

if __name__ == "__main__":
    main()