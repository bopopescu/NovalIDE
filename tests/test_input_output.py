# -*- coding: gbk -*-
def discount(price,rate): 
    final_price=price*rate
    return  final_price
old_price=float(input('������ԭ�ۣ�'))
rate=float(input('�������ۿ��ʣ�'))
new_price=discount(old_price,rate)
print('���ۺ�۸��ǣ�',new_price)