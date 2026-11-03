from fnb.queue import Node, Queue


def test_queue_starts_empty():
    queue = Queue[int]()
    assert queue.is_empty()
    assert queue.size() == 0
    assert queue.peek() is None
    assert queue.dequeue() is None


def test_queue_uses_linked_nodes_and_fifo():
    queue = Queue[str]()
    queue.enqueue("Burger")
    queue.enqueue("Coca")
    queue.enqueue("Pho")

    assert isinstance(queue.front, Node)
    assert isinstance(queue.rear, Node)
    assert queue.front.data == "Burger"
    assert queue.front.next.data == "Coca"
    assert queue.rear.data == "Pho"
    assert queue.size() == 3
    assert queue.peek() == "Burger"
    assert queue.dequeue() == "Burger"
    assert queue.dequeue() == "Coca"
    assert queue.dequeue() == "Pho"
    assert queue.is_empty()
    assert queue.front is None
    assert queue.rear is None


def test_queue_can_enqueue_after_becoming_empty():
    queue = Queue[int]()
    queue.enqueue(1)
    assert queue.dequeue() == 1
    queue.enqueue(2)
    assert queue.peek() == 2
    assert queue.dequeue() == 2


def test_to_list_does_not_change_queue():
    queue = Queue[int]()
    queue.enqueue(1)
    queue.enqueue(2)
    assert queue.to_list() == [1, 2]
    assert queue.size() == 2
