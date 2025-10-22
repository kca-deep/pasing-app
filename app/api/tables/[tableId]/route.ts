import { NextRequest, NextResponse } from 'next/server';
import { readFile } from 'fs/promises';
import { join } from 'path';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ tableId: string }> }
) {
  try {
    const { tableId } = await params;

    // Get document name from query parameter
    const searchParams = request.nextUrl.searchParams;
    const docName = searchParams.get('doc');

    if (!docName) {
      return NextResponse.json(
        { error: 'Document name is required' },
        { status: 400 }
      );
    }

    // Construct path to table JSON file
    // Format: output/{doc_name}/tables/{table_id}.json
    const outputDir = join(process.cwd(), '..', 'output', docName, 'tables');
    const tablePath = join(outputDir, `${tableId}.json`);

    // Read and parse the JSON file
    const fileContent = await readFile(tablePath, 'utf-8');
    const tableData = JSON.parse(fileContent);

    return NextResponse.json(tableData);
  } catch (error: any) {
    console.error('Error loading table data:', error);

    if (error.code === 'ENOENT') {
      return NextResponse.json(
        { error: 'Table not found' },
        { status: 404 }
      );
    }

    return NextResponse.json(
      { error: 'Failed to load table data' },
      { status: 500 }
    );
  }
}
