# Library Management System - Project Planning

## 1. Project Overview

A library management system that handles:
- Book management and inventory tracking
- Reader/patron management
- Lending and returning of books
- Book ordering/reservations system

---

## 2. Core Requirements

### 2.1 Book Borrowing
- **Constraint:** A reader can hold a maximum of **4 copies** at any time
- **Order Closure:** When a book is borrowed as a result of an order, the order is automatically closed
- **Status tracking:** Track borrowed books per reader

### 2.2 Book Return
- **Reserved Returns:** When an ordered book copy is returned, it is reserved for the person who ordered it
- **Cancellation Rule:** If the reserved book is not borrowed within **3 days**, the order is automatically cancelled
- **Return processing:** Log return transactions and update availability

### 2.3 Book Ordering
- **Order Creation:** A reader can order a book (only if the book exists in the system)
- **Order Status:** Track order status (pending, fulfilled, cancelled)
- **Availability Check:** Verify book exists before allowing order

---

## 3. Domain Model

### 3.1 Core Entities

#### Reader (Patron)
- `id`: unique identifier
- `name`: reader name
- `email`: contact email
- `phone`: contact phone
- `registration_date`: when reader registered
- `active_borrowings`: count of currently borrowed copies (max 4)
- `status`: active/inactive

#### Book
- `id`: unique identifier
- `title`: book title
- `author`: author name
- `isbn`: ISBN number (unique)
- `description`: book description
- `publication_date`: publication date
- `total_copies`: total copies in library
- `available_copies`: copies available for borrowing

#### Copy (Book Instance)
- `id`: unique identifier
- `book_id`: reference to Book
- `status`: available/borrowed/reserved
- `location`: physical location in library
- `acquisition_date`: when added to library

#### Borrowing/Loan
- `id`: unique identifier
- `reader_id`: reference to Reader
- `copy_id`: reference to Copy
- `order_id`: reference to Order (optional - if from order)
- `borrow_date`: when borrowed
- `due_date`: when due
- `return_date`: actual return date
- `status`: active/returned

#### Order/Reservation
- `id`: unique identifier
- `reader_id`: reference to Reader
- `book_id`: reference to Book
- `order_date`: when ordered
- `status`: pending/fulfilled/cancelled
- `fulfilled_date`: when order was fulfilled
- `cancellation_date`: when cancelled
- `reserved_copy_id`: reserved copy (optional)
- `reservation_expiry_date`: 3 days from reservation

---

## 4. Business Rules & Workflows

### 4.1 Borrowing Workflow
```
1. Reader requests to borrow a book
2. Check: Reader has < 4 active borrowings
3. Check: Copy is available (not borrowed, not reserved)
4. Create Borrowing record
5. Update Copy status to "borrowed"
6. Decrement Book.available_copies
7. If borrow was from Order → close the Order
```

### 4.2 Return Workflow
```
1. Reader returns a copy
2. Find associated Borrowing record
3. Check: Is there an Order for this Book?
4. If Order exists:
   a. Mark Copy as "reserved"
   b. Link Copy to Order (reserved_copy_id)
   c. Set reservation_expiry_date = now + 3 days
   d. Update Order status
5. If no Order:
   a. Mark Copy as "available"
   b. Increment Book.available_copies
6. Update Borrowing status to "returned"
7. Log return transaction
```

### 4.3 Reservation Expiry Workflow
```
1. Check all Orders with reserved copies
2. If reservation_expiry_date < now:
   a. Mark Order as "cancelled"
   b. Mark reserved Copy as "available"
   c. Increment Book.available_copies
   d. Clear reserved_copy_id from Order
```

### 4.4 Ordering Workflow
```
1. Reader requests to order a book
2. Check: Book exists in system
3. Check: Reader doesn't already have active order for this book
4. Create Order record with status "pending"
5. If available_copies > 0:
   a. Can immediately borrow if < 4 borrowings
   b. Close order on borrow
6. If no copies available:
   a. Order remains pending
   b. Wait for return and reservation
```

---

## 5. Database Schema (Preliminary)

### Tables

#### readers
```sql
CREATE TABLE readers (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE,
  phone VARCHAR(20),
  registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
  status ENUM('active', 'inactive') DEFAULT 'active'
)
```

#### books
```sql
CREATE TABLE books (
  id INT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(255) NOT NULL,
  author VARCHAR(255),
  isbn VARCHAR(20) UNIQUE,
  description TEXT,
  publication_date DATE,
  total_copies INT DEFAULT 0,
  available_copies INT DEFAULT 0
)
```

#### copies
```sql
CREATE TABLE copies (
  id INT PRIMARY KEY AUTO_INCREMENT,
  book_id INT NOT NULL,
  status ENUM('available', 'borrowed', 'reserved') DEFAULT 'available',
  location VARCHAR(255),
  acquisition_date DATE DEFAULT CURRENT_DATE,
  FOREIGN KEY (book_id) REFERENCES books(id)
)
```

#### borrowings
```sql
CREATE TABLE borrowings (
  id INT PRIMARY KEY AUTO_INCREMENT,
  reader_id INT NOT NULL,
  copy_id INT NOT NULL,
  order_id INT,
  borrow_date DATETIME DEFAULT CURRENT_TIMESTAMP,
  due_date DATE,
  return_date DATETIME,
  status ENUM('active', 'returned') DEFAULT 'active',
  FOREIGN KEY (reader_id) REFERENCES readers(id),
  FOREIGN KEY (copy_id) REFERENCES copies(id),
  FOREIGN KEY (order_id) REFERENCES orders(id)
)
```

#### orders
```sql
CREATE TABLE orders (
  id INT PRIMARY KEY AUTO_INCREMENT,
  reader_id INT NOT NULL,
  book_id INT NOT NULL,
  order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
  status ENUM('pending', 'fulfilled', 'cancelled') DEFAULT 'pending',
  fulfilled_date DATETIME,
  cancellation_date DATETIME,
  reserved_copy_id INT,
  reservation_expiry_date DATETIME,
  FOREIGN KEY (reader_id) REFERENCES readers(id),
  FOREIGN KEY (book_id) REFERENCES books(id),
  FOREIGN KEY (reserved_copy_id) REFERENCES copies(id)
)
```

---

## 6. Core Features/API Endpoints (Preliminary)

### Reader Management
- `POST /api/readers` - Create new reader
- `GET /api/readers/{id}` - Get reader details
- `GET /api/readers/{id}/borrowings` - Get reader's active borrowings
- `GET /api/readers/{id}/orders` - Get reader's orders

### Book Management
- `POST /api/books` - Add new book
- `GET /api/books` - List books
- `GET /api/books/{id}` - Get book details
- `POST /api/books/{id}/copies` - Add copies to book

### Borrowing Management
- `POST /api/borrowings` - Borrow a book (check constraints)
- `GET /api/borrowings/{id}` - Get borrowing details
- `PUT /api/borrowings/{id}/return` - Return a book

### Order Management
- `POST /api/orders` - Create order
- `GET /api/orders/{id}` - Get order details
- `PUT /api/orders/{id}/cancel` - Cancel order
- `GET /api/orders/expiring` - Get orders about to expire

### Admin/Maintenance
- `POST /api/admin/process-expired-reservations` - Process expired orders

---

## 7. Implementation Plan

### Phase 1: Foundation
- [ ] Set up project structure
- [ ] Design database schema
- [ ] Create database tables
- [ ] Set up ORM/persistence layer

### Phase 2: Core Entities
- [ ] Implement Reader model and CRUD operations
- [ ] Implement Book model and CRUD operations
- [ ] Implement Copy model and CRUD operations

### Phase 3: Borrowing System
- [ ] Implement Borrowing model
- [ ] Create borrow validation logic (4-copy limit check)
- [ ] Implement borrowing creation
- [ ] Implement basic return functionality

### Phase 4: Order/Reservation System
- [ ] Implement Order model
- [ ] Create order creation logic
- [ ] Implement reservation logic on return
- [ ] Create expiry check and cancellation logic

### Phase 5: Advanced Features
- [ ] Implement order closure on borrow
- [ ] Add reservation expiry background job
- [ ] Add comprehensive validation
- [ ] Add error handling and logging

### Phase 6: Testing & Documentation
- [ ] Unit tests for business logic
- [ ] Integration tests for workflows
- [ ] API documentation
- [ ] User documentation

### Phase 7: Deployment
- [ ] Setup CI/CD pipeline
- [ ] Deploy to production
- [ ] Monitor and maintain

---

## 8. Key Validations

### When Borrowing:
- ✓ Reader has < 4 active borrowings
- ✓ Copy is available (status = 'available')
- ✓ Reader is active

### When Returning:
- ✓ Borrowing record exists
- ✓ Copy belongs to reader's borrowing

### When Ordering:
- ✓ Book exists
- ✓ Reader is active
- ✓ Reader doesn't have pending order for same book

### When Processing Expiry:
- ✓ Order status is 'pending' with reserved copy
- ✓ Reservation expiry date has passed

---

## 9. Constraints & Assumptions

| Constraint | Details |
|-----------|---------|
| Max Borrowings | 4 copies per reader |
| Reservation Duration | 3 days |
| Book Requirement | Book must exist in system to order |
| Status Flow | Clear workflow for each entity's status changes |

---

## 10. Notes & Considerations

- **Concurrency:** Consider database locking for borrowing operations
- **Notifications:** Consider notifying readers when their orders are ready
- **Late Returns:** Current spec doesn't cover late fees; scope for future
- **Book Ratings:** Could add reader reviews/ratings in future
- **Wishlist:** Could implement user wishlist feature
- **Background Jobs:** Reservation expiry processing should run periodically (e.g., daily)

---

## 11. Progress Tracking

Use this section to track implementation progress:

- [ ] Phase 1 Complete
- [ ] Phase 2 Complete
- [ ] Phase 3 Complete
- [ ] Phase 4 Complete
- [ ] Phase 5 Complete
- [ ] Phase 6 Complete
- [ ] Phase 7 Complete

Last Updated: 2026-09-08
