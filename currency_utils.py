# SmartFinance AI - Centralized Currency Formatting Utility (INR)

CURRENCY_CODE = 'INR'
CURRENCY_SYMBOL = '₹'
CURRENCY_NAME = 'Indian Rupee'
CURRENCY_LOCALE = 'en-IN'

def format_inr(amount, decimals=2, include_symbol=True):
    """
    Format numeric value into Indian Rupee (INR) representation:
    e.g., 100000 -> '₹1,00,000.00' (or '1,00,000.00' if include_symbol is False)
    Negative values format as '-₹1,000.00'
    """
    if amount is None:
        amount = 0.0
    try:
        val = float(amount)
    except (ValueError, TypeError):
        prefix = CURRENCY_SYMBOL if include_symbol else ''
        return f"{prefix}0.00" if decimals > 0 else f"{prefix}0"

    is_negative = val < 0
    val = abs(val)

    # Format with requested decimals
    formatted_str = f"{val:.{decimals}f}" if decimals > 0 else f"{int(round(val))}"
    parts = formatted_str.split('.')
    integer_part = parts[0]
    decimal_part = ('.' + parts[1]) if len(parts) > 1 and decimals > 0 else ''

    # Apply Indian numbering system (last 3 digits, then groups of 2)
    if len(integer_part) > 3:
        last_three = integer_part[-3:]
        remaining = integer_part[:-3]
        groups = []
        while remaining:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        formatted_int = ','.join(groups) + ',' + last_three
    else:
        formatted_int = integer_part

    symbol = CURRENCY_SYMBOL if include_symbol else ''
    result = f"{symbol}{formatted_int}{decimal_part}"
    return f"-{result}" if is_negative else result


def format_inr_compact(amount):
    """
    Compact representation for charts or small badges:
    e.g., 1500000 -> '₹15L', 25000000 -> '₹2.5Cr', 45000 -> '₹45k'
    """
    try:
        val = float(amount)
    except (ValueError, TypeError):
        return f"{CURRENCY_SYMBOL}0"

    abs_val = abs(val)
    sign = '-' if val < 0 else ''

    if abs_val >= 10000000:  # 1 Crore
        return f"{sign}{CURRENCY_SYMBOL}{abs_val / 10000000:.2f} Cr"
    elif abs_val >= 100000:  # 1 Lakh
        return f"{sign}{CURRENCY_SYMBOL}{abs_val / 100000:.2f} L"
    elif abs_val >= 1000:
        return f"{sign}{CURRENCY_SYMBOL}{abs_val / 1000:.1f} k"
    else:
        return format_inr(val, decimals=0)

