# Alembic Revision

Run in `ichrisbirch/ichrisbirch` (where `alembic.ini` is located)

## First Run

```bash
export ENVIRONMENT='development' # or 'production'
alembic revision --autogenerate -m 'Create initial tables'
alembic upgrade head
```

## Subsequent Runs

1. Make the changes to the models and schemas

2. Run a revision to pickup changes in code
`alembic revision --autogenerate -m 'Add notes field to tasks table'`

    > **Note**  
    > If this doesn't work perfectly, you must edit the revision file

3. Run the upgrade in the environments

!!! note "Locally"
    ```bash
    export ENVIRONMENT='development'
    alembic upgrade head
    ```

!!! info "EC2"
    ```bash
    export ENVIRONMENT='production'
    alembic upgrade head
    ```

## Troubleshooting

***Error***  
Alembic is not able to upgrade to the latest because the revisions got out of sync.  

***Solution***  
Find the last revision that was successfully run (manually by inspecting the database) and then run:
`alembic stamp <revision>` to set the current revision to the last successful one.
Then run the upgrade again:
`alembic upgrade head`

## sqlalchemy create_all vs alembic upgrade

`SQLAlchemy` and `Alembic` are two powerful tools in the Python ecosystem used for database handling and migrations, respectively. They are often used together in projects to manage database schemas and perform database operations. Understanding the difference between `SQLAlchemy`'s `create_all` method and `Alembic`'s `upgrade` function is crucial for effectively managing database schema changes and migrations.

### `SQLAlchemy.create_all`

`SQLAlchemy` is an SQL toolkit and Object-Relational Mapping (ORM) library for Python. It provides a full suite of well known enterprise-level persistence patterns, designed for efficient and high-performing database access.

- **What it does**: The `create_all` method in `SQLAlchemy` is used to create all tables that have been defined in your SQLAlchemy models but don't yet exist in the database. It doesn't consider the current state of the database schema. Instead, it blindly attempts to create all the tables (and associated schema elements like indexes) based on the models you've defined. If a table already exists, it simply skips the creation for that table.
- **Usage scenario**: `create_all` is particularly useful in simple projects or during the initial setup of a project's database where you are starting with an empty database and want to construct the schema based on your models' definitions.

### `Alembic.upgrade`

`Alembic` is a lightweight database migration tool for usage with `SQLAlchemy`. It allows you to manage changes to your database schema over time, enabling versioning of your database similarly to how you version your source code.

- **What it does**: The `upgrade` function in Alembic applies one or more migrations (changes) to the database schema, moving it to a new version. These migrations are written as scripts which define how to apply a change (e.g., add a table, alter a column) and how to revert it. The `upgrade` command considers the current version of your database and applies all new migrations in sequence up to the latest version or to a specified version.
- **Usage scenario**: `Alembic.upgrade` is used in iterative development and production environments where the state of the database schema evolves over time. It ensures that schema changes are applied in a controlled and versioned manner, allowing for smooth transitions across different versions of your schema as your application grows and changes.

### Key Differences

- **Version control**: Alembic allows for version-controlled schema changes, making it possible to migrate your database schema forwards or backwards as needed. `SQLAlchemy.create_all` does not consider versions of your schema.
- **Sensitivity to existing schema**: `create_all` essentially ignores the current schema state (it won't modify or delete existing tables), while Alembic `upgrade` scripts can be tailored to alter the current schema precisely and incrementally.
- **Purpose and scope**: `create_all` is a more blunt instrument, best suited for initial schema creation. Alembic, with its `upgrade` (and corresponding `downgrade`) commands, supports a more nuanced and controlled approach to database schema evolution.

In summary, while `SQLAlchemy.create_all` is useful for initial schema creation in simple scenarios, `Alembic.upgrade` provides a robust framework for managing schema changes over time in a version-controlled, incremental, and reversible manner. For complex projects and in production environments, integrating Alembic for migration management alongside SQLAlchemy for ORM capabilities is considered best practice.

### How to deal with database that has got out of sync with alembic revisions and alembic report Target database is not up to date.  How to find what version of the revision the database matches

When your database schema has gotten out of sync with Alembic revisions, the message "Target database is not up to date" typically indicates Alembic detects mismatches between the expected schema version (from your migration scripts) and the current state of your database. Handling this scenario involves a few steps to identify the disparity and resolve it. Here's how you can approach this situation:

### 1. Identify Current Database Version

First, check the current schema version of your database. Alembic uses a table (`alembic_version` by default) to track the current revision of the schema in your database.

You can manually check this table:

```sql
SELECT * FROM alembic_version;
```

Or use Alembic's `current` command:

```shell
alembic current
```

This command displays the current revision that the database is on.

### 2. Compare with Alembic Revision History

Next, list all the revisions known to Alembic to see where the current database version stands in relation to the migration history.

Run the following command to show your migrations history:

```shell
alembic history
```

This command will print a list of revisions. Find where the revision from your database fits within this list. This will inform you whether the database is ahead, behind, or has diverged (if the current revision doesn't exist in your migration chain).

### 3. Identify Divergences or Missing Revisions

If the database's current revision doesn't exist in the migration history from `alembic history`, it suggests that the database might have applied a revision that has since been deleted or was created from a different branch of your code.

In cases where the database is behind, and simply applying newer migrations is required, you can proceed to use `alembic upgrade` with the target revision you want to apply.

However, if the database is ahead or has diverged, you need to assess how to reconcile the differences.

### 4. Resolving Divergences

#### Option A: Manually adjust the database/schema

If possible, manually adjust the database schema to match a specific version in your Alembic history, and use `alembic stamp` to mark it as such, without applying migrations. This can be necessary if the database was manually altered.

```shell
alembic stamp <revision_id>
```

#### Option B: Generate a new migration

You can attempt to autogenerate a new migration that takes into account the current state of the database and the desired state as per your models.

Run:

```shell
alembic revision --autogenerate -m "Fixing divergence"
```

Review the generated script closely, as it may not be perfect and could require manual adjustments.

#### Option C: Revert to a known good state

If all else fails and you have the ability to reset your database to a known good state (usually viable only in development or with available backups), you can revert the database back to a specific revision and reapply migrations from there.

### 5. Apply Missing Migrations

After resolving discrepancies, ensure that your database is at the correct revision and that all necessary migrations are applied.

```shell
alembic upgrade head
```

### Caution

Dealing with schema mismatches can lead to data loss or corruption if not handled carefully. Always back up your database before attempting to resolve discrepancies and thoroughly test any changes in a safe environment prior to application in production.

Navigating database schema issues can be challenging, but by systematically checking the current state, comparing it with your migration history, and carefully applying corrections, you can resolve discrepancies and get your project back on track.

### continue

### 6. Validate Schema After Adjustments

After applying the necessary adjustments and migrations, it’s essential to validate that the database schema now matches the expectations of your application and Alembic migrations. Conduct thorough testing to ensure that:

- All expected tables, columns, indexes, and other database objects are correctly defined.
- The application can successfully interact with the database without encountering schema-related errors.
- Running `alembic current` reports the correct and expected revision.

### 7. Consider Future Prevention Strategies

To avoid future discrepancies between your database schema and Alembic revisions, consider implementing strategies that ensure better synchronization and tracking:

- **Continuous Integration (CI) Checks**: Implement CI pipelines that run tests against a database that is always migrated from scratch using current Alembic migrations. This helps catch issues where migrations do not match the application models or are missing.
- **Code Review Processes**: Incorporate migration script reviews as part of your development process to catch potential issues early on.
- **Restricted Database Access**: Limit who can manually alter the database schema. Ideally, all changes should go through Alembic migrations to ensure that the schema evolution is recorded and versioned.
- **Documenting Manual Changes**: In the unavoidable scenario where manual database changes are made, document these changes meticulously. Consider creating corresponding Alembic migrations, even if they are marked as already applied, to ensure the migration history remains an accurate record of the schema's evolution.

### 8. Additional Tools and Practices

- **Alembic Autogenerate Revisions**: While the `--autogenerate` feature is powerful, it should not be blindly trusted. Always review the generated migration scripts to ensure they accurately represent the desired schema changes and do not inadvertently drop or alter objects.
- **Model Comparison Extensions**: For complex projects, consider using or developing tools that help compare the SQLAlchemy models directly against the actual database schema, identifying discrepancies without relying solely on Alembic's version history.
- **Regular Audits**: Schedule regular audits of your database schema versus your models and migrations. This proactive approach can help identify issues before they become problematic.
- **Environment Parity**: Aim for parity between your development, staging, and production environments in terms of how migrations are applied and managed, reducing the risk of discrepancies arising from differences in how environments are handled.

### Conclusion

Getting a database schema back in sync with Alembic revisions involves careful diagnosis, proper tool usage, and strategic resolution of discrepancies. It requires a clear understanding of your current schema state, how it deviates from the expected state, and the steps needed to safely reconcile these differences. Implementing preventative strategies and maintaining meticulous records of changes are key to minimizing future synchronization issues, ensuring that your database schema evolution remains manageable, trackable, and aligned with your application's requirements.

## How Does Alembic Determine the Order of Migrations

Alembic determines the order in which to apply migrations using a couple of key concepts: **revision identifiers** and **down_revision attributes** within the migration scripts. These elements create a directed acyclic graph (DAG) of migrations, establishing a clear lineage or path through your migration history. Here's how these components work together to manage migration order:

### Revision Identifiers

Each Alembic migration script is assigned a unique revision identifier (often a hash) when the migration is generated. This identifier uniquely distinguishes each migration in the series of changes made over time.

### Down Revision Attribute

Within each migration script, there's an attribute named `down_revision`. This attribute specifies the identifier of the migration that directly precedes the current one in the migration history. The `down_revision` effectively points back to the migration's parent in the version history tree.

For the very first migration in a project, `down_revision` will be `None`, indicating that there is no parent migration (i.e., it's the root of the migration tree).

### Upgrade and Downgrade Sequences

Given these two components, Alembic constructs a sequence of migrations:

- **Upgrade**: To migrate forward, Alembic starts from the earliest migration whose `down_revision` is `None` and follows the chain of `revision` to `down_revision` links, applying each migration in turn until it reaches the specified target migration or the latest migration if no target is specified.

- **Downgrade**: For migrating backward, Alembic reverses the process, using the current revision as a starting point and following the chain of `down_revision` values in reverse to apply the `downgrade()` operations defined in each migration script, until it reaches the specified target revision.

### Handling Branches

Alembic also supports branching in migrations. When branches are present, there may be multiple migration scripts with the same `down_revision`. In this scenario, Alembic uses a "merge" migration to bring the divergent branches back into a single linear path. The merge migration specifies multiple `down_revision` values, identifying each of the branch tips that it reconciles.

When applying migrations:

1. **Linear Migrations**: In simple, linear migrations, Alembic applies migrations in the straightforward sequence dictated by the single parent-child (`down_revision` to `revision`) relationships.

2. **Branched Migrations**: In branched scenarios, Alembic will apply migrations from each branch as required, until it encounters a merge point. At the merge point, it ensures that all required branches are up to date before applying the merge migration, thus reconciling the branches and continuing forward in a linear fashion from there.

### Version Table

Alembic tracks the current version of the database schema in the `alembic_version` table, recording which migrations have been applied. This table is crucial for determining the starting point for any migration operation, be it an upgrade or downgrade.

In summary, Alembic determines the order of migrations through a combination of unique revision identifiers, parent-child (down_revision) relationships creating a logical sequence, and support for merging branched histories. This structure allows Alembic to manage complex migrations histories with precision and ensure the database schema evolves coherently with the application's requirements.

## Removing a Revision That Has Not Been Applied to the Database

If you have an Alembic revision that hasn't been applied to any database yet and you wish to remove it, the process is fairly straightforward since you only need to deal with the revision script(s) in your migrations folder. Here's how you can do it:

### Steps to Remove an Unapplied Alembic Revision

1. **Locate the Revision File**: In your project, navigate to the `versions` directory within your Alembic migrations folder. This folder contains all the revision scripts generated by Alembic.

2. **Identify the Revision Script**: Each file in the `versions` directory corresponds to a specific revision. The filename usually starts with the revision ID (a sequence of letters and numbers generated by Alembic) followed by an underscore and a brief description of the migration, e.g., `ae1027a6acf_migration_description.py`. Identify the script file for the revision you wish to remove. Make sure this is the correct revision by opening the file and verifying its contents, including the revision ID, the `down_revision`, and the changes it introduces.

3. **Delete the Revision File**: Simply delete the identified Python script file from the `versions` directory. This removes the revision from your migrations history, as far as Alembic is concerned.

4. **Check if Downstream Revisions Exist**: If the revision you're removing has "child" revisions (i.e., revisions that list it as their `down_revision`), you will need to decide how to handle those. You cannot simply delete a revision if later revisions depend on it without risking inconsistencies in your migration path. If such downstream revisions exist, consider the following options:
   - **Delete the Downstream Revisions Too**: If the downstream revisions also haven't been applied and aren't necessary, you can delete them as well.
   - **Rebase the Downstream Revisions**: If the downstream revisions need to be kept, you may need to edit their `down_revision` attributes to reflect the removal of the parent revision. This might involve setting their `down_revision` to the removed revision's parent or to a new merge revision if the history is more complex.

5. **Regenerate Dependency Graph (Optional)**: If you modified the `down_revision` of any subsequent migrations, or if you're not sure about the consistency of your migration scripts, you might want to regenerate the Alembic dependency graph. However, this is more about verifying that your revisions are consistent and there are no “orphaned” migrations. Alembic doesn't automatically generate a visual graph, but you can check consistency by running `alembic history` to make sure it outputs a coherent history from your base revision to the head, without any missing links.

6. **Update Database Schema Manually if Necessary**: If the deleted migration or any of its downstream migrations had been applied to any other environment's database (development, staging, etc.), you'll need to manually adjust those database schemas and possibly the `alembic_version` table to ensure consistency. This step applies only if the migration was mistakenly said to be unapplied when, in fact, it had been applied somewhere.

### Delete Caution

- Be extra careful to ensure that the migration has indeed not been applied to any environment. Removing applied migrations can lead to inconsistencies and errors.
- Always have a backup of your database and current migration scripts before deleting or modifying them.
- Remember to communicate with your team about any changes to the migration scripts, especially if other developers might have applied the deleted migration in their local environment.

In summary, removing an unapplied Alembic revision is as simple as deleting its script file from the `versions` directory, but care should be taken to handle dependency and consistency issues that might arise from doing so.
