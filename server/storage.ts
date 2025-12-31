import { posts, posters, type Post, type InsertPost, type Poster, type InsertPoster } from "@shared/schema";
import { db } from "./db";
import { eq, desc } from "drizzle-orm";

export interface IStorage {
  // Posts
  getPost(id: number): Promise<Post | undefined>;
  getPostByGuid(guid: string): Promise<Post | undefined>;
  createPost(post: InsertPost): Promise<Post>;
  getAllPosts(): Promise<Post[]>;

  // Posters (Captions)
  getPoster(id: number): Promise<Poster | undefined>;
  createPoster(poster: InsertPoster): Promise<Poster>;
  getPosters(): Promise<(Poster & { post: Post })[]>;
}

export class DatabaseStorage implements IStorage {
  async getPost(id: number): Promise<Post | undefined> {
    const [post] = await db.select().from(posts).where(eq(posts.id, id));
    return post;
  }

  async getLatestPost(): Promise<Post | undefined> {
    const [post] = await db.select().from(posts).orderBy(desc(posts.pubDate)).limit(1);
    return post;
  }

  async getPostByGuid(guid: string): Promise<Post | undefined> {
    const [post] = await db.select().from(posts).where(eq(posts.guid, guid));
    return post;
  }

  async createPost(insertPost: InsertPost): Promise<Post> {
    const [post] = await db.insert(posts).values(insertPost).returning();
    return post;
  }

  async getAllPosts(): Promise<Post[]> {
    return await db.select().from(posts).orderBy(desc(posts.pubDate));
  }

  async getPoster(id: number): Promise<Poster | undefined> {
    const [poster] = await db.select().from(posters).where(eq(posters.id, id));
    return poster;
  }

  async createPoster(insertPoster: InsertPoster): Promise<Poster> {
    const [poster] = await db.insert(posters).values(insertPoster).returning();
    return poster;
  }

  async getPosters(): Promise<(Poster & { post: Post })[]> {
    const result = await db
      .select({
        poster: posters,
        post: posts,
      })
      .from(posters)
      .innerJoin(posts, eq(posters.postId, posts.id))
      .orderBy(desc(posters.createdAt));
    
    return result.map(row => ({
      ...row.poster,
      post: row.post,
    }));
  }
}

export const storage = new DatabaseStorage();
