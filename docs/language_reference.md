# QXL Language Reference

## Program Structure

Every QXL program must be wrapped in `start` and `end` keywords:

```qxl
start
    // your code here
end
```

## Data Types

| Type      | Description            | Example          |
|-----------|------------------------|------------------|
| `number`  | Integer                | `42`, `-7`       |
| `decimal` | Floating-point         | `3.14`, `0.5`    |
| `text`    | String (double-quoted) | `"Hello"`        |
| `bool`    | Boolean                | `true`, `false`  |

## Variable Declaration

```qxl
number x = 10
decimal pi = 3.14
text name = "Alice"
bool active = true
```

Uninitialized variables get default values:
- `number` → `0`
- `decimal` → `0.0`
- `text` → `""`
- `bool` → `false`

## Assignment

```qxl
x = 42
name = "Bob"
```

## Output

```qxl
show "Hello, World!"
show x + y
show 3.14
```

## Input

```qxl
read variableName
```

## Operators

### Arithmetic
| Operator | Description    |
|----------|----------------|
| `+`      | Addition       |
| `-`      | Subtraction    |
| `*`      | Multiplication |
| `/`      | Division       |
| `%`      | Modulus        |

### Comparison
| Operator | Description          |
|----------|----------------------|
| `>`      | Greater than         |
| `<`      | Less than            |
| `>=`     | Greater or equal     |
| `<=`     | Less or equal        |
| `==`     | Equal                |
| `!=`     | Not equal            |

### Logical
| Operator | Description |
|----------|-------------|
| `&&`     | AND         |
| `\|\|`  | OR          |
| `!`      | NOT         |

## Conditional (If/Otherwise)

```qxl
if x > 10
    show "big"
endif

if x > 10
    show "big"
otherwise
    show "small"
endif
```

## Loops (Repeat)

```qxl
repeat condition
    // body
endrepeat
```

Use `break` to exit a loop and `continue` to skip to the next iteration.

```qxl
number i = 0
repeat i < 10
    i = i + 1
    if i == 5
        break
    endif
    show i
endrepeat
```

## Functions

```qxl
function add(number a, number b)
    return a + b
endfunction

// Call
show add(3, 4)
```

Functions can:
- Accept typed parameters
- Return values using `return`
- Be called before their declaration (forward references)

## Comments

```qxl
// Single-line comment

/* 
   Multi-line
   comment
*/
```
