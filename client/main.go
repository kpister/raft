package main

import (
    "log"
    "fmt"
    "time"
    "context"

    "google.golang.org/grpc"
    kv "github.com/kpister/raft/kvstore"
)

func messagePut(c kv.KeyValueStoreClient, key string, value string) {
    fmt.Printf("Putting value: %d", value)
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()

    // build request
    req := &kv.PutRequest{
        Key: key,
        Value: value,
    }

    res, _ := c.Put(ctx, req)
    fmt.Printf("Status code: %d", res.Ret)
}

func messageGet(c kv.KeyValueStoreClient, key string) string {
    fmt.Printf("Getting value for key %s", key)
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()

    // build request
    req := &kv.GetRequest {
        Key: key,
    }

    res, _ := c.Get(ctx, req)
    fmt.Printf("Status code: %d", res.Ret)
    fmt.Printf("Value: %s", res.Value)
    return res.Value
}

const (
    servAddr = "localhost:5000"
)

func main() {
    conn, err := grpc.Dial(servAddr, grpc.WithInsecure())
    if err != nil {
        log.Fatalf("Failed to connect: %v", err)
    }
    defer conn.Close()

    client := kv.NewKeyValueStoreClient(conn)
    messagePut(client, "m", "1")
    messageGet(client, "m")
}