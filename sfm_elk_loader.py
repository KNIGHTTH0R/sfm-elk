from sfmutils.consumer import BaseConsumer, MqConfig, EXCHANGE
from subprocess import check_output, CalledProcessError
import logging
import argparse

log = logging.getLogger(__name__)


class ElkLoader(BaseConsumer):
    def __init__(self, collection_set_id=None, mq_config=None):
        BaseConsumer.__init__(self, mq_config=mq_config)
        self.collection_set_id = collection_set_id
        if self.collection_set_id:
            log.info("Limiting to collection sets %s", self.collection_set_id)
        else:
            log.info("Not limiting by collection set.")

    def on_message(self):
        # Message should be WARC created
        warc_filepath = self.message["warc"]["path"]
        if self.collection_set_id and self.collection_set_id != self.message["collection_set"]["id"]:
            log.info("Skipping %s because it is from a different collection set", warc_filepath)
            return
        harvest_type = self.message["harvest"]["type"]
        if harvest_type in ('twitter_search', 'twitter_user_timeline'):
            iter_type = "twitter_rest_warc_iter.py --elkwarc=true"
        elif harvest_type in ('twitter_sample', 'twitter_filter'):
            iter_type = "twitter_stream_warc_iter.py --elkwarc=true"
        elif harvest_type in ('weibo_timeline', 'weibo_search'):
            iter_type = "weibo_warc_iter.py --elkwarc=true"
        else:
            log.info("Skipping %s because there is not yet a warc iterator for harvest type %s", warc_filepath,
                     harvest_type)
            return
        log.info("Loading %s", warc_filepath)
        cmd = "{} {} | /usr/share/logstash/bin/logstash -f stdin.conf".format(iter_type, warc_filepath)

        try:
            check_output(cmd, shell=True)
            log.info("Loading %s completed.", warc_filepath)
        except CalledProcessError, e:
            log.error("%s returned %s: %s", cmd, e.returncode, e.output)


if __name__ == "__main__":
    # Logging
    logging.basicConfig(format='%(asctime)s: %(name)s --> %(message)s', level=logging.DEBUG)

    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("host")
    parser.add_argument("username")
    parser.add_argument("password")
    parser.add_argument("queue")
    parser.add_argument("--collection-set", help="Limit to load to collection set with this collection set id.")
    parser.add_argument("--debug", type=lambda v: v.lower() in ("yes", "true", "t", "1"), nargs="?",
                        default="False", const="True")

    args = parser.parse_args()

    # Logging
    logging.getLogger().setLevel(logging.DEBUG if args.debug else logging.INFO)

    # Adding a queue name that is prefixed with this host. This will allow sending messages directly
    # to this queue. This approach could be generalized so that the queue specific binding is created
    # and the queue name is automatically removed.
    loader = ElkLoader(collection_set_id=args.collection_set,
                       mq_config=MqConfig(args.host, args.username, args.password, EXCHANGE,
                                          {args.queue: ["warc_created", "{}.warc_created".format(args.queue)]}))
    loader.run()
