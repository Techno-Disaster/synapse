/* Copyright 2022 Beeper
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

-- Each of these are denormalised copies of `stream_ordering` from the corresponding row in` events` which
-- we use to improve database performance by reduring JOINs.
ALTER TABLE current_state_events ADD COLUMN event_stream_ordering BIGINT REFERENCES events(stream_ordering);
ALTER TABLE local_current_membership ADD COLUMN event_stream_ordering BIGINT REFERENCES events(stream_ordering);
ALTER TABLE room_memberships ADD COLUMN event_stream_ordering BIGINT REFERENCES events(stream_ordering);
