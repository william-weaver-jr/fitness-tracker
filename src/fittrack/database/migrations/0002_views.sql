-- Migration 0002: JSON Duality Views
-- Provides document-style access with relational integrity (Oracle 23ai feature).
-- All application reads/writes flow through these views — never raw table DML.

-- ─── User + Profile composite view ───────────────────────────────────────────
CREATE OR REPLACE JSON RELATIONAL DUALITY VIEW user_profile_dv AS
SELECT JSON {
    '_id'          : u.user_id,
    'email'        : u.email,
    'status'       : u.status,
    'role'         : u.role,
    'pointBalance' : u.point_balance,
    'version'      : u.version,
    'emailVerified': u.email_verified,
    'lastLoginAt'  : u.last_login_at,
    'createdAt'    : u.created_at,
    'updatedAt'    : u.updated_at,
    'profile'      : (
        SELECT JSON {
            'profileId'        : p.profile_id,
            'displayName'      : p.display_name,
            'dateOfBirth'      : p.date_of_birth,
            'stateOfResidence' : p.state_of_residence,
            'biologicalSex'    : p.biological_sex,
            'ageBracket'       : p.age_bracket,
            'fitnessLevel'     : p.fitness_level,
            'tierCode'         : p.tier_code,
            'heightInches'     : p.height_inches,
            'weightPounds'     : p.weight_pounds
        }
        FROM profiles p WITH INSERT UPDATE DELETE
        WHERE p.user_id = u.user_id
    ),
    'connections'  : [
        SELECT JSON {
            'connectionId' : c.connection_id,
            'provider'     : c.provider,
            'isPrimary'    : c.is_primary,
            'lastSyncAt'   : c.last_sync_at,
            'syncStatus'   : c.sync_status
        }
        FROM tracker_connections c WITH INSERT UPDATE DELETE
        WHERE c.user_id = u.user_id
    ]
}
FROM users u WITH INSERT UPDATE DELETE
/

-- ─── Drawing + Prizes composite view ─────────────────────────────────────────
CREATE OR REPLACE JSON RELATIONAL DUALITY VIEW drawing_dv AS
SELECT JSON {
    '_id'              : d.drawing_id,
    'drawingType'      : d.drawing_type,
    'name'             : d.name,
    'description'      : d.description,
    'ticketCostPoints' : d.ticket_cost_points,
    'drawingTime'      : d.drawing_time,
    'ticketSalesClose' : d.ticket_sales_close,
    'eligibility'      : d.eligibility,
    'status'           : d.status,
    'totalTickets'     : d.total_tickets,
    'createdAt'        : d.created_at,
    'updatedAt'        : d.updated_at,
    'completedAt'      : d.completed_at,
    'prizes'           : [
        SELECT JSON {
            'prizeId'         : p.prize_id,
            'rank'            : p.rank,
            'name'            : p.name,
            'description'     : p.description,
            'valueUsd'        : p.value_usd,
            'quantity'        : p.quantity,
            'fulfillmentType' : p.fulfillment_type,
            'imageUrl'        : p.image_url
        }
        FROM prizes p WITH INSERT UPDATE DELETE
        WHERE p.drawing_id = d.drawing_id
    ]
}
FROM drawings d WITH INSERT UPDATE DELETE
/

-- ─── Activity summary view (per user, per day) ────────────────────────────────
CREATE OR REPLACE JSON RELATIONAL DUALITY VIEW activity_dv AS
SELECT JSON {
    '_id'          : a.activity_id,
    'userId'       : a.user_id,
    'connectionId' : a.connection_id,
    'externalId'   : a.external_id,
    'activityType' : a.activity_type,
    'startTime'    : a.start_time,
    'endTime'      : a.end_time,
    'durationMinutes': a.duration_minutes,
    'intensity'    : a.intensity,
    'metrics'      : a.metrics,
    'pointsEarned' : a.points_earned,
    'processed'    : a.processed,
    'createdAt'    : a.created_at
}
FROM activities a WITH INSERT UPDATE DELETE
/
