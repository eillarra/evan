---
applyTo: '**/*.vue,**/*.ts'
description: Vue 3, Quasar, and Pinia coding standards with strict behavioral testing guidelines.
---

## Core architecture

- **Framework:** Vue 3.
- **API:** Composition API with `<script setup lang="ts">` is mandatory.
- **Package manager:** Use `yarn` for all package management commands.
- **State management:** Pinia is the only state management library.

## Reactivity best practices

### Choosing the right ref type

| Type         | Use for                                                   | Example                          |
| :----------- | :-------------------------------------------------------- | :------------------------------- |
| `ref`        | Primitives, small objects where deep reactivity is needed | `ref(0)`, `ref({ name: '' })`    |
| `shallowRef` | Large arrays, objects from API responses                  | `shallowRef<User[]>([])`         |
| `readonly`   | Exposing state that shouldn't be mutated                  | `readonly(state)` in composables |

### Guidelines

- **API responses:** Always use `shallowRef` for data fetched from APIs to avoid performance costs of deep reactivity.
- **Updating shallowRef:** Always replace the `.value` entirely.
- **Async calls:** Use `unawaited()` from `src/utils/errorHandler` for fire-and-forget calls. Never use `void`.

## Component structure

- **File order:** `<style scoped>`, then `<template>`, then `<script setup>`.
- **Naming:** `PascalCase.vue` for components, `useSomething.ts` for composables.
- **Quasar:** Always prefer Quasar components (`<q-btn>`) over native HTML. Use Quasar utility classes (`q-pa-md`, `row`) instead of custom CSS.

## Code organization for testability

### Pure functions vs Composables

- **Pure functions (src/utils/):** Stateless. No Vue imports.
- **Composables (src/composables/):** Stateful. Use Vue reactivity.

### Extracting logic

Do not write complex transformation logic inside `<script setup>`. Extract it to pure functions (utils) or composables so it can be tested in isolation.

## Testing philosophy

We test **behavior**, not functions. We test **boundaries**, not external libraries.

### The "black box" rule

Test the public API of your classes or modules. Do not test private methods or internal implementation details. If you refactor the internal code but the output remains the same, tests should not break.

### The "not our code" rule

We assume external libraries work as advertised. Do not write tests to verify standard library behavior.

- ❌ Testing the library: Asserting that `moment(date).format()` returns a string tests Moment.js, not us.
- ❌ Testing the mock: Mocking a function and asserting it returns what you told it to return.
- ✅ Testing integration: Asserting that _our_ code handles the library's success/failure correctly.

### Functionality over implementation

Test _what_ the result is, not _how_ we got it. Don't spy on internal method calls.

```typescript
// ❌ BAD: Brittle, tied to implementation
it('should call validateInput then calculateTax', () => {
  const spy1 = vi.spyOn(service, 'validateInput');
  service.processOrder(100);
  expect(spy1).toHaveBeenCalled();
});

// ✅ GOOD: Robust, tests behavior
it('should return the total price including 20% tax', () => {
  const result = service.processOrder(100);
  expect(result.total).toBe(120);
});
```

### Boundary testing

When using external libraries, mock the **boundary**, not the logic. Test _our reaction_ to external success/failure.

```typescript
// ❌ BAD: Testing if our mock works
it('axios should return data', async () => {
  mockAxios.get.mockResolvedValue({ data: 'foo' });
  const result = await axios.get('/url');
  expect(result.data).toBe('foo');
});

// ✅ GOOD: Testing our error handling
it('should throw CustomLibError when the network fails', async () => {
  mockAxios.get.mockRejectedValue(new Error('Network Error'));
  await expect(myLibrary.fetchData()).rejects.toThrow(CustomLibError);
});
```

### Testing composables (the public API)

Composables usually don't need to be mounted in a component to be tested.

```typescript
// ✅ Good Composable Test
describe('usePagination', () => {
  it('navigates to the next page', () => {
    const { page, nextPage } = usePagination({ total: 100 });

    nextPage();

    expect(page.value).toBe(2);
  });
});
```
