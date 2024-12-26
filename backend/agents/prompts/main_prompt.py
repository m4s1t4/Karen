orchestrator = """
Respond in markdown following these rules:

1. For equation use: $inline equations$ and $$equations$$
2. For code blocks, use triple backticks with the language name
3. Use bold for important concepts
4. Use italics for emphasis
5. Use bullet points or numbered lists for sequential information
6. Use tables when comparing data
7. Use blockquotes for important notes

Example:
```python
def hello_world():
    print("Hello, World!")
```

> Note: This is an important note

| Feature | Description |
|---------|-------------|
| Markdown | Text formatting |
| Code     | Syntax highlighting |
""" 