# Hướng dẫn Khắc phục lỗi Metrics trong Insight

## Tóm tắt vấn đề đã khắc phục

**Vấn đề**: Khi edit insight từ trang insights, phần metrics bị mất hoặc không lưu được thông tin ban đầu.

**Nguyên nhân**: 
- Form không xử lý JSON metrics đúng cách
- Views không đảm bảo metrics được lưu khi edit
- Template không hiển thị metrics đúng format

## Các thay đổi đã thực hiện

### 1. Cải thiện InsightForm (`finance_dashboard/forms.py`)

**Thêm method `clean_metrics()`**:
```python
def clean_metrics(self):
    """Validate metrics JSON format"""
    metrics = self.cleaned_data.get('metrics')
    if not metrics:
        return None
    
    # Nếu metrics là string, thử parse JSON
    if isinstance(metrics, str):
        try:
            import json
            parsed_metrics = json.loads(metrics)
            return parsed_metrics
        except json.JSONDecodeError:
            raise forms.ValidationError("Metrics must be valid JSON format")
    
    return metrics
```

**Cải thiện widget**:
```python
'metrics': forms.Textarea(attrs={'rows': 2, 'placeholder': '{"pnl": 100, "drawdown": 5}'}),
```

### 2. Sửa lỗi trong các Views

**Edit Insight View** (`edit_insight`):
```python
# Lưu form với xử lý metrics
insight = form.save(commit=False)

# Đảm bảo metrics được lưu đúng
if 'metrics' in form.cleaned_data:
    insight.metrics = form.cleaned_data['metrics']

insight.save()
```

**Create Insight for Portfolio** (`create_insight_for_portfolio`):
```python
insight = form.save(commit=False)
insight.portfolio_ref = portfolio

# Đảm bảo metrics được lưu đúng
if 'metrics' in form.cleaned_data:
    insight.metrics = form.cleaned_data['metrics']

insight.save()
```

**Trade Insight Modal** (`trade_insight_modal`):
```python
insight = form.save(commit=False)
insight.portfolio_ref = trade.portfolio

# Đảm bảo metrics được lưu đúng
if 'metrics' in form.cleaned_data:
    insight.metrics = form.cleaned_data['metrics']

insight.save()
```

**Create Insight from Trade** (`create_insight_from_trade`):
```python
# Sử dụng form để tạo insight
form = InsightForm(request.POST, request.FILES)
if form.is_valid():
    insight = form.save(commit=False)
    insight.portfolio_ref = trade.portfolio
    
    # Đảm bảo metrics được lưu đúng
    if 'metrics' in form.cleaned_data:
        insight.metrics = form.cleaned_data['metrics']
    
    insight.save()
```

### 3. Cải thiện Template

**Edit Insight Modal** (`edit_insight_modal.html`):
```html
<textarea class="form-control" id="id_metrics" name="metrics" rows="2" 
          placeholder='{"pnl": 100, "drawdown": 5}'>
    {% if insight.metrics %}{% if insight.metrics|length > 0 %}{{ insight.metrics|safe }}{% endif %}{% endif %}
</textarea>
<div class="form-text">Enter valid JSON format, e.g., {"pnl": 100, "drawdown": 5}</div>
```

## Cách test và đảm bảo metrics hoạt động đúng

### Bước 1: Test tạo insight mới với metrics

1. **Tạo insight từ trang Insights**:
   - Vào `/insights/`
   - Click "Create Insight"
   - Điền thông tin và metrics JSON: `{"pnl": 100, "drawdown": 5}`
   - Save và kiểm tra xem metrics có được lưu không

2. **Tạo insight từ trang Portfolio**:
   - Vào `/portfolio/`
   - Click "Add Insight" cho một portfolio
   - Điền thông tin và metrics JSON
   - Save và kiểm tra xem metrics có được lưu không

### Bước 2: Test edit insight với metrics

1. **Edit insight từ trang Insights**:
   - Vào `/insights/`
   - Click vào một insight có metrics
   - Click "Edit"
   - Sửa metrics: `{"pnl": 200, "drawdown": 10, "win_rate": 75}`
   - Save và kiểm tra xem metrics có được cập nhật không

2. **Edit insight từ trang Portfolio**:
   - Vào `/portfolio/`
   - Click "Edit" cho insight của portfolio
   - Sửa metrics
   - Save và kiểm tra xem metrics có được cập nhật không

### Bước 3: Test các trường hợp edge case

1. **Metrics rỗng**:
   - Tạo insight với metrics rỗng
   - Edit và thêm metrics
   - Kiểm tra xem có lỗi không

2. **Metrics JSON không hợp lệ**:
   - Tạo insight với metrics: `{"pnl": 100, "drawdown": 5` (thiếu dấu })
   - Kiểm tra xem có hiển thị lỗi validation không

3. **Metrics với các kiểu dữ liệu khác nhau**:
   - Test với string: `{"strategy": "scalping"}`
   - Test với number: `{"pnl": 100.5}`
   - Test với boolean: `{"is_profitable": true}`
   - Test với array: `{"trades": [1, 2, 3]}`

### Bước 4: Kiểm tra hiển thị metrics

1. **Trong modal insight**:
   - Click vào insight để xem chi tiết
   - Kiểm tra xem metrics có hiển thị đúng format không

2. **Trong template insights**:
   - Vào `/insights/`
   - Kiểm tra xem metrics có hiển thị trong danh sách không

## Các file đã thay đổi

- `finance_dashboard/forms.py` - Thêm `clean_metrics()` method
- `finance_dashboard/views.py` - Sửa lỗi xử lý metrics trong các views
- `finance_dashboard/templates/finance_dashboard/partials/edit_insight_modal.html` - Cải thiện hiển thị metrics

## Lưu ý quan trọng

1. **JSON Format**: Metrics phải là JSON hợp lệ
2. **Validation**: Form sẽ validate JSON format trước khi lưu
3. **Error Handling**: Có xử lý lỗi khi JSON không hợp lệ
4. **Backward Compatibility**: Các insight cũ vẫn hoạt động bình thường

## Kết quả mong đợi

Sau khi triển khai:

1. ✅ Tạo insight mới với metrics hoạt động bình thường
2. ✅ Edit insight giữ nguyên metrics ban đầu
3. ✅ Metrics được hiển thị đúng format trong modal
4. ✅ Validation JSON hoạt động đúng
5. ✅ Không có lỗi khi metrics rỗng hoặc không hợp lệ

## Troubleshooting

### Nếu metrics vẫn bị mất:

1. **Kiểm tra browser console**:
   - Mở Developer Tools (F12)
   - Xem có lỗi JavaScript không

2. **Kiểm tra Django logs**:
   - Xem logs trên Render
   - Tìm lỗi liên quan đến metrics

3. **Test với JSON đơn giản**:
   - Thử với: `{"test": "value"}`
   - Kiểm tra xem có lưu được không

### Nếu validation lỗi:

1. **Kiểm tra JSON format**:
   - Đảm bảo có dấu ngoặc kép
   - Đảm bảo có dấu phẩy đúng chỗ
   - Đảm bảo không có dấu phẩy cuối

2. **Test với JSON validator**:
   - Copy JSON vào https://jsonlint.com/
   - Kiểm tra xem có hợp lệ không
