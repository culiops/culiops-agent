package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/aws/aws-sdk-go-v2/aws"
	awsconfig "github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/sns"
	"github.com/aws/aws-sdk-go-v2/service/sqs"
)

type server struct {
	sns      *sns.Client
	topicArn string
	sqs      *sqs.Client
	ledgerQ  string
}

func main() {
	ctx := context.Background()
	cfg, err := awsconfig.LoadDefaultConfig(ctx)
	if err != nil {
		log.Fatalf("aws config: %v", err)
	}
	s := &server{
		sns:      sns.NewFromConfig(cfg),
		topicArn: os.Getenv("CART_EVENTS_TOPIC_ARN"),
		sqs:      sqs.NewFromConfig(cfg),
		ledgerQ:  os.Getenv("LEDGER_QUEUE_URL"),
	}
	http.HandleFunc("/healthz", func(w http.ResponseWriter, _ *http.Request) { w.WriteHeader(http.StatusOK) })
	http.HandleFunc("/checkout", s.checkout)
	log.Fatal(http.ListenAndServe(":"+os.Getenv("PORT"), nil))
}

func (s *server) checkout(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	orderID, total := placeOrder(r)

	if err := s.publishCartEvent(ctx, orderID); err != nil {
		log.Printf("WARN cart event publish failed (non-fatal): %v", err)
	}
	if err := s.recordLedger(ctx, orderID, total); err != nil {
		// Ledger entries feed nightly finance reconciliation.
		log.Printf("WARN ledger send failed (non-fatal): %v", err)
	}
	w.WriteHeader(http.StatusCreated)
}

func (s *server) publishCartEvent(ctx context.Context, orderID string) error {
	_, err := s.sns.Publish(ctx, &sns.PublishInput{
		TopicArn: aws.String(s.topicArn),
		Message:  aws.String(orderID),
	})
	return err
}

func (s *server) recordLedger(ctx context.Context, orderID string, total int64) error {
	body, _ := json.Marshal(map[string]any{"order_id": orderID, "total": total})
	_, err := s.sqs.SendMessage(ctx, &sqs.SendMessageInput{
		QueueUrl:               aws.String(s.ledgerQ),
		MessageBody:            aws.String(string(body)),
		MessageGroupId:         aws.String("ledger"),
	})
	if err != nil {
		return fmt.Errorf("sqs send: %w", err)
	}
	return nil
}

func placeOrder(r *http.Request) (string, int64) { return "ord-1", 4200 }
