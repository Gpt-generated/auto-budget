# Kişisel Ev Bütçesi (Flask)

Bu proje, ev bütçenizi yönetebilmeniz için basit fakat genişletilebilir bir Flask uygulaması sunar. Aşağıdaki temel modüller desteklenir:

- **Harcamalar** – Harcamaları kaydedebilir, bir harcamayı parçalarına bölebilir veya taksit bilgisi girebilirsiniz.
- **Harcama Kaynakları** – Harcama kaynağını (kredi kartı, nakit, borç vb.) tanımlayabilirsiniz.
- **Borçlar** – Borçlarınızı izleyebilirsiniz.
- **Gelirler** – Maaş veya ek gelirleri kaydedebilirsiniz.

## Başlangıç

```bash
python -m venv .venv
source .venv/bin/activate  # Windows için: .venv\\Scripts\\activate
pip install -r requirements.txt
flask --app app --debug run
```

İlk defa çalıştırmadan önce örnek verilerle veritabanını başlatabilirsiniz:

```bash
flask --app app init-db
```

Bu komut `budget.db` dosyasını oluşturur ve örnek gelir/harcama/borç kayıtları ekler.

## API Uç Noktaları

| Yöntem | Yol | Açıklama |
| --- | --- | --- |
| GET | `/` | API hakkında bilgi verir |
| GET/POST | `/sources` | Harcama kaynaklarını listele/ekle |
| GET/PUT/DELETE | `/sources/<id>` | Kaynak detayları |
| GET/POST | `/expenses` | Harcamaları listele/ekle (bölme ve taksit desteği) |
| GET/PUT/DELETE | `/expenses/<id>` | Harcama detayları |
| GET/POST | `/incomes` | Gelirleri listele/ekle |
| GET/PUT/DELETE | `/incomes/<id>` | Gelir detayları |
| GET/POST | `/debts` | Borçları listele/ekle |
| GET/PUT/DELETE | `/debts/<id>` | Borç detayları |

### Örnek İstek: Taksitli Harcama

```bash
curl -X POST http://localhost:5000/expenses \
  -H "Content-Type: application/json" \
  -d '{
        "description": "Laptop",
        "amount": 24000,
        "date": "2024-04-18",
        "category": "Teknoloji",
        "source_id": 1,
        "installment": {"count": 12, "number": 1, "amount": 2000},
        "splits": [
            {"name": "İş", "amount": 16000},
            {"name": "Kişisel", "amount": 8000}
        ]
      }'
```

Uygulama JSON çıktıları döndürür ve böylece frontend veya mobil bir uygulama tarafından kolayca tüketilebilir.

## Test

Projede hazır bir test takımı bulunmuyor. Değişiklik yaptıktan sonra en azından kodun sözdizimini kontrol etmek için aşağıdaki komutu çalıştırabilirsiniz:

```bash
python -m compileall .
```

## Lisans

MIT lisansı altında dağıtılmaktadır.
